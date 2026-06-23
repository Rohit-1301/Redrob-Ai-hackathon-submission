import os
import sys
import json
import csv
import logging
import numpy as np

# Setup path to import configs and other local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from SelectedCandidates.src.utils.jd_parser import parse_jd
from SelectedCandidates.src.semantic.embeddings import (
    load_embedding_model,
    get_or_compute_embeddings,
    build_faiss_index
)
from SelectedCandidates.src.scoring.score_engine import (
    calculate_career_score,
    calculate_skill_score,
    calculate_behavior_score,
    calculate_quality_score,
    calculate_product_company_score
)
from SelectedCandidates.src.explainability.explainer import (
    generate_brief_reasoning,
    generate_detailed_explanation
)

logger = logging.getLogger(__name__)

def load_all_eligible_candidates(valid_path: str, review_path: str, weak_path: str) -> list:
    """
    Loads candidates from valid, review, and weak JSON splits.
    Attaches their category for scoring purposes.
    """
    logger.info("Loading candidates from preprocessed JSON splits...")
    candidates = []
    
    # Load Valid
    if os.path.exists(valid_path):
        with open(valid_path, 'r', encoding='utf-8') as f:
            valid_list = json.load(f)
            for c in valid_list:
                c["ranking_category"] = "VALID"
            candidates.extend(valid_list)
        logger.info(f"Loaded {len(valid_list)} candidates from VALID split.")
        
    # Load Review
    if os.path.exists(review_path):
        with open(review_path, 'r', encoding='utf-8') as f:
            review_list = json.load(f)
            for c in review_list:
                c["ranking_category"] = "REVIEW"
            candidates.extend(review_list)
        logger.info(f"Loaded {len(review_list)} candidates from REVIEW split.")
        
    # Load Weak
    if os.path.exists(weak_path):
        with open(weak_path, 'r', encoding='utf-8') as f:
            weak_list = json.load(f)
            for c in weak_list:
                c["ranking_category"] = "WEAK"
            candidates.extend(weak_list)
        logger.info(f"Loaded {len(weak_list)} candidates from WEAK split.")
        
    return candidates

def run_ranking_pipeline(
    docx_path: str,
    valid_path: str,
    review_path: str,
    weak_path: str,
    output_dir: str,
    cache_dir: str
) -> dict:
    """
    Executes the cascaded ranking and selection process.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    
    # 1. Parse JD to extract competencies
    jd_analysis_path = os.path.join(output_dir, "../data/jd_analysis.json")
    jd_analysis = parse_jd(docx_path, jd_analysis_path)
    
    # 2. Load all eligible candidates
    candidates = load_all_eligible_candidates(valid_path, review_path, weak_path)
    if not candidates:
        raise ValueError("No candidates loaded. Check preprocessed split paths.")
        
    # 3. Stage 1: Non-semantic scoring & Lossless Pre-filtering
    logger.info("Stage 1: Computing non-semantic candidate profiles...")
    candidate_non_semantic_scores = []
    
    for cand in candidates:
        # Calculate individual component scores (fast lookups)
        career = calculate_career_score(cand)
        skill = calculate_skill_score(cand)
        behavior = calculate_behavior_score(cand)
        quality = calculate_quality_score(cand)
        prod_comp = calculate_product_company_score(cand)
        
        # Non-semantic component sum (weighted)
        non_sem_score = (
            0.20 * career["score"] +
            0.15 * skill["score"] +
            0.10 * behavior["score"] +
            0.10 * quality["score"] +
            0.05 * prod_comp
        )
        
        # Apply category multipliers
        cat = cand["ranking_category"].upper()
        if cat == "VALID":
            multiplier = 1.00
        elif cat == "REVIEW":
            multiplier = 0.85
        elif cat == "WEAK":
            multiplier = 0.60
        else:
            multiplier = 0.00
            
        # Check honeypot
        honeypot_score = cand.get("honeypot_score", 0)
        is_honeypot = honeypot_score > 80 or "honeypot" in str(cand.get("flags", [])).lower()
        
        # Calculate maximum potential score assuming semantic match is 1.0
        max_potential_score = (non_sem_score + 0.40) * multiplier
        if is_honeypot:
            max_potential_score -= 999.0
            
        candidate_non_semantic_scores.append({
            "candidate": cand,
            "non_semantic_score": non_sem_score,
            "multiplier": multiplier,
            "category": cat,
            "is_honeypot": is_honeypot,
            "max_potential_score": max_potential_score,
            "components": {
                "career": career,
                "skill": skill,
                "behavior": behavior,
                "quality": quality,
                "product_company_score": prod_comp
            }
        })
        
    # Sort candidates by maximum potential score descending
    candidate_non_semantic_scores.sort(key=lambda x: -x["max_potential_score"])
    
    # Select subset to embed (lossless threshold: 400 candidates is extremely safe)
    subset_size = min(400, len(candidate_non_semantic_scores))
    logger.info(f"Filtering down from {len(candidates)} to top {subset_size} candidates for Stage 2 semantic embedding.")
    selected_subset = candidate_non_semantic_scores[:subset_size]
    
    # 4. Stage 2: Semantic Similarity & Embedding Generation
    model = load_embedding_model()
    cache_path = os.path.join(cache_dir, "embeddings.pkl")
    
    # Extract raw candidate profiles for subset
    subset_candidates = [item["candidate"] for item in selected_subset]
    embeddings, candidate_ids = get_or_compute_embeddings(subset_candidates, model, cache_path)
    
    # 5. FAISS Indexing & Search
    faiss_index_path = os.path.join(cache_dir, "faiss/index.faiss")
    index = build_faiss_index(embeddings, faiss_index_path)
    
    # Build query text for JD
    jd_text = (
        f"Title: {jd_analysis['title']}\n"
        f"Experience Preferred: {jd_analysis['experience_preferred']}\n"
        f"Required Competencies: {', '.join(jd_analysis['required_competencies'])}\n"
        f"Preferred Competencies: {', '.join(jd_analysis['preferred_competencies'])}"
    )
    logger.info("Computing embedding for the parsed Job Description...")
    jd_embedding = model.encode([jd_text], normalize_embeddings=True)[0]
    
    # Run vector similarity query via FAISS
    logger.info("Running FAISS vector query for candidate semantic matching...")
    query_vector = np.array([jd_embedding], dtype='float32')
    distances, indices = index.search(query_vector, len(selected_subset))
    
    # Map candidate_id to semantic similarity score
    semantic_scores = {}
    for idx, dist in zip(indices[0], distances[0]):
        if 0 <= idx < len(candidate_ids):
            cand_id = candidate_ids[idx]
            semantic_scores[cand_id] = float(dist)
            
    # 6. Compute Final Hybrid Scores for Subset
    logger.info("Blending semantic matching into final hybrid scores...")
    scored_candidates = []
    
    for item in selected_subset:
        cand = item["candidate"]
        cand_id = cand["candidate_id"]
        sem_score = semantic_scores.get(cand_id, 0.0)
        multiplier = item["multiplier"]
        is_honeypot = item["is_honeypot"]
        non_sem = item["non_semantic_score"]
        
        raw_hybrid_score = non_sem + 0.40 * sem_score
        final_score = raw_hybrid_score * multiplier
        if is_honeypot:
            final_score -= 999.0
            
        # Format final scored candidate info
        scored_info = {
            "candidate_id": cand_id,
            "final_score": round(max(-999.0, final_score), 4),
            "raw_hybrid_score": round(raw_hybrid_score, 4),
            "multiplier": multiplier,
            "category": item["category"],
            "is_honeypot": is_honeypot,
            "semantic_score": round(sem_score, 4),
            "career_score": round(item["components"]["career"]["score"], 4),
            "skill_score": round(item["components"]["skill"]["score"], 4),
            "behavior_score": round(item["components"]["behavior"]["score"], 4),
            "quality_score": round(item["components"]["quality"]["score"], 4),
            "product_company_score": item["components"]["product_company_score"],
            "career_details": item["components"]["career"]["details"],
            "skill_details": item["components"]["skill"]["details"],
            "behavior_details": item["components"]["behavior"]["details"],
            "quality_details": item["components"]["quality"]["details"]
        }
        scored_candidates.append((cand, scored_info))
        
    # 7. Sorting & Tie-breaking
    # Primary: final_score descending
    # Secondary: candidate_id ascending
    logger.info("Sorting and ranking candidates...")
    scored_candidates.sort(key=lambda x: (-x[1]["final_score"], x[1]["candidate_id"]))
    
    # 8. Select Top 100 and write output files
    top_100 = scored_candidates[:100]
    logger.info(f"Top candidate score: {top_100[0][1]['final_score']:.4f}")
    logger.info(f"100th candidate score: {top_100[99][1]['final_score']:.4f}")
    
    # CSV generation
    csv_path = os.path.join(output_dir, "top_100_candidates.csv")
    logger.info(f"Writing Top 100 candidates to CSV: {csv_path}")
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        
        for rank_idx, (cand, scored_info) in enumerate(top_100, 1):
            brief_reason = generate_brief_reasoning(scored_info)
            writer.writerow([
                scored_info["candidate_id"],
                rank_idx,
                f"{scored_info['final_score']:.4f}",
                brief_reason
            ])
            
    # Detailed explanations JSON generation
    explanations_path = os.path.join(output_dir, "top_100_explanations.json")
    logger.info(f"Writing detailed explanations to JSON: {explanations_path}")
    explanations = []
    for rank_idx, (cand, scored_info) in enumerate(top_100, 1):
        det_explain = generate_detailed_explanation(scored_info, rank_idx)
        # Store profile highlights in explanation
        det_explain["profile_highlights"] = {
            "name": cand.get("profile", {}).get("anonymized_name", ""),
            "headline": cand.get("profile", {}).get("headline", ""),
            "summary": cand.get("profile", {}).get("summary", ""),
            "location": cand.get("profile", {}).get("location", ""),
            "current_title": cand.get("profile", {}).get("current_title", ""),
            "current_company": cand.get("profile", {}).get("current_company", "")
        }
        explanations.append(det_explain)
        
    with open(explanations_path, 'w', encoding='utf-8') as f:
        json.dump(explanations, f, indent=2, ensure_ascii=False)
        
    logger.info("Ranking pipeline run completed successfully.")
    
    return {
        "top_100": top_100,
        "csv_path": csv_path,
        "explanations_path": explanations_path
    }
