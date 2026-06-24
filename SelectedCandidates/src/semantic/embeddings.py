import os
import pickle
import logging
import numpy as np
import faiss
import torch
from sentence_transformers import SentenceTransformer

# Optimize PyTorch CPU execution
torch.set_num_threads(4)

logger = logging.getLogger(__name__)

def load_embedding_model():
    """
    Loads BAAI/bge-small-en-v1.5, falling back to all-MiniLM-L6-v2 if necessary.
    """
    try:
        logger.info("Loading semantic embedding model: BAAI/bge-small-en-v1.5")
        model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    except Exception as e:
        logger.warning(f"Could not load BAAI/bge-small-en-v1.5: {e}. Falling back to all-MiniLM-L6-v2.")
        model = SentenceTransformer('all-MiniLM-L6-v2')
    return model

def build_candidate_text(candidate: dict) -> str:
    """
    Constructs a textual representation of the candidate for semantic embedding.
    """
    profile = candidate.get("profile", {})
    headline = profile.get("headline", "")
    summary = profile.get("summary", "")
    
    skills = candidate.get("skills", [])
    skills_str = ", ".join([s.get("name", "") for s in skills if isinstance(s, dict)])
    
    career = candidate.get("career_history", [])
    career_list = []
    for job in career:
        if not isinstance(job, dict):
            continue
        title = job.get("title", "")
        comp = job.get("company", "")
        career_list.append(f"{title} at {comp}")
    career_str = ", ".join(career_list)
    
    text = f"Headline: {headline}. Summary: {summary}. Skills: {skills_str}. Experience: {career_str}."
    return text

def get_or_compute_embeddings(candidates: list, model, cache_path: str) -> np.ndarray:
    """
    Retrieves candidate embeddings from cache, or computes and caches them if not present.
    """
    if os.path.exists(cache_path):
        logger.info(f"Loading candidate embeddings from cache: {cache_path}")
        with open(cache_path, 'rb') as f:
            data = pickle.load(f)
            # Verify cache integrity vs candidate count
            if len(data.get("candidate_ids", [])) == len(candidates):
                return data["embeddings"], data["candidate_ids"]
            else:
                logger.warning("Cache size mismatch, recomputing embeddings...")
                
    logger.info(f"Computing semantic embeddings for {len(candidates)} candidates...")
    texts = [build_candidate_text(c) for c in candidates]
    
    # Encode with sentence-transformers
    embeddings = model.encode(texts, batch_size=256, show_progress_bar=True, normalize_embeddings=True)
    candidate_ids = [c.get("candidate_id") for c in candidates]
    
    # Save cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump({"embeddings": embeddings, "candidate_ids": candidate_ids}, f)
        
    logger.info("Semantic embeddings saved to cache.")
    return embeddings, candidate_ids

def build_faiss_index(embeddings: np.ndarray, index_path: str) -> faiss.IndexFlatIP:
    """
    Builds and persists a FAISS IndexFlatIP for vector search.
    """
    logger.info("Building FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    
    # Add L2 normalized embeddings (embeddings are already normalized)
    index.add(embeddings.astype('float32'))
    
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    faiss.write_index(index, index_path)
    logger.info(f"FAISS index persisted at: {index_path}")
    return index
