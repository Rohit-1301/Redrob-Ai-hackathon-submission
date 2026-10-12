import os
import re
import json
import logging
from typing import Dict, Any, Union, BinaryIO

logger = logging.getLogger(__name__)

# Common taxonomy of technical skills and frameworks for robust extraction
COMMON_TECH_SKILLS = [
    # Languages
    "python", "java", "c++", "c#", "golang", "go", "rust", "javascript", "typescript", "scala", "ruby", "sql", "r", "bash",
    # ML & AI
    "machine learning", "deep learning", "nlp", "natural language processing", "llm", "large language models",
    "embeddings", "vector databases", "vector database", "faiss", "pinecone", "weaviate", "qdrant", "milvus", "chroma", "chromadb",
    "retrieval", "ranking", "search", "recommendation", "dense retrieval", "sparse retrieval", "hybrid search",
    "learning-to-rank", "learning to rank", "ltr", "reranking", "cross-encoder", "bi-encoder", "bm25",
    "pytorch", "tensorflow", "keras", "scikit-learn", "xgboost", "lightgbm", "catboost", "huggingface", "transformers",
    "fine-tuning", "peft", "lora", "qlora", "rlhf", "dpo", "langchain", "llamaindex", "vllm", "ollama",
    "evaluation", "ndcg", "mrr", "map", "rag", "retrieval-augmented generation",
    # Data & Search Engines
    "elasticsearch", "opensearch", "solr", "spark", "pyspark", "kafka", "flink", "hadoop", "airflow",
    "postgres", "postgresql", "mysql", "mongodb", "redis", "cassandra", "snowflake", "bigquery",
    # Systems & Cloud
    "docker", "kubernetes", "k8s", "aws", "gcp", "azure", "linux", "distributed systems", "microservices",
    "rest api", "grpc", "graphql", "fastapi", "flask", "django", "ci/cd", "terraform", "git",
    # Frontend (for fullstack/frontend roles)
    "react", "react.js", "vue", "angular", "node.js", "html", "css", "tailwind"
]

def extract_text_from_file(file_obj_or_path: Union[str, BinaryIO, bytes], filename: str = "") -> str:
    """
    Extracts text from PDF, DOCX, or TXT file object, bytes, or file path.
    """
    if isinstance(file_obj_or_path, str):
        path = file_obj_or_path
        filename = filename or os.path.basename(path)
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, "rb") as f:
            file_bytes = f.read()
    elif isinstance(file_obj_or_path, bytes):
        file_bytes = file_obj_or_path
    elif hasattr(file_obj_or_path, "read"):
        file_bytes = file_obj_or_path.read()
        if hasattr(file_obj_or_path, "seek"):
            file_obj_or_path.seek(0)
    else:
        file_bytes = b""

    fn_lower = filename.lower()
    text = ""

    # 1. PDF
    if fn_lower.endswith(".pdf") or file_bytes.startswith(b"%PDF"):
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pages = [page.get_text() for page in doc]
            text = "\n".join(pages)
            if text.strip():
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}. Trying pypdf...")
            
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
            if text.strip():
                return text
        except Exception as e:
            logger.error(f"pypdf extraction failed: {e}")

    # 2. DOCX
    elif fn_lower.endswith(".docx") or fn_lower.endswith(".doc"):
        try:
            import io
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    paras.append(" ".join(c.text.strip() for c in row.cells if c.text.strip()))
            text = "\n".join(paras)
            if text.strip():
                return text
        except Exception as e:
            logger.error(f"python-docx extraction failed: {e}")

    # 3. Plain Text fallback
    try:
        text = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        text = str(file_bytes)

    return text

def parse_jd_content(raw_text: str, source_name: str = "Uploaded JD") -> Dict[str, Any]:
    """
    Intelligently parses JD text to extract:
    - Title / Role
    - Experience requirement (min, max, label)
    - Required & Preferred skills
    - Locations & Disqualifiers
    - Semantic search representation
    """
    text = raw_text.strip()
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # 1. Detect Job Title
    title = ""
    title_patterns = [
        r"(?:job\s*description|job\s*title|position|role|title)\s*[:\-–]\s*([^\n\r]+)",
        r"(?:hiring\s+for|looking\s+for\s+a(?:n)?)\s*[:\-–]?\s*([^\n\r]+)",
        r"^([A-Z][A-Za-z0-9\s\(\)\/\-\+]{4,40}(?:Engineer|Developer|Scientist|Architect|Lead|Manager|Specialist|Analyst))",
    ]
    for pattern in title_patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            extracted_title = m.group(1).split("\n")[0].strip()
            # Clean up trailing dashes or subtitles like " — Founding Team"
            cleaned_title = re.split(r"\s+[—–\-|]\s+", extracted_title)[0].strip()
            if 3 <= len(cleaned_title) <= 60:
                title = cleaned_title
                break

    if not title:
        # Fallback to inspecting the first 5 lines
        for line in lines[:5]:
            if any(term in line.lower() for term in ["engineer", "developer", "scientist", "architect", "lead"]):
                title = re.sub(r"^(job description|jd|opening|role)\s*[:\-–]?\s*", "", line, flags=re.I).strip()
                break

    if not title:
        title = "Senior AI Engineer (Ranking & Retrieval)" if "ranking" in text.lower() or "retrieval" in text.lower() else "Software Engineer"

    # 2. Detect Experience Requirements
    min_exp, max_exp = 5.0, 9.0  # default
    exp_patterns = [
        r"(\d+(?:\.\d+)?)\s*(?:–|-|to)\s*(\d+(?:\.\d+)?)\s*(?:years|yrs)",
        r"(\d+(?:\.\d+)?)\s*\+\s*(?:years|yrs)",
        r"at\s+least\s+(\d+(?:\.\d+)?)\s*(?:years|yrs)",
        r"minimum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(?:years|yrs)"
    ]
    for pattern in exp_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            if len(m.groups()) == 2 and m.group(2):
                min_exp = float(m.group(1))
                max_exp = float(m.group(2))
            else:
                min_exp = float(m.group(1))
                max_exp = min_exp + 4.0
            break

    exp_label = f"{int(min_exp) if min_exp.is_integer() else min_exp}–{int(max_exp) if max_exp.is_integer() else max_exp} years"

    # 3. Detect Skills & Competencies
    # Look for sections
    lower_text = text.lower()
    
    # Split text into sections if possible
    req_section_match = re.search(r"(?:requirements|must have|required qualifications|what you(?:'ll)? need|qualifications|core competencies)[:\n](.*?)(?:preferred|good to have|nice to have|bonus|benefits|about us|\Z)", lower_text, re.DOTALL)
    pref_section_match = re.search(r"(?:preferred|good to have|nice to have|bonus points?|plus points?|desired)[:\n](.*?)(?:benefits|about us|what we offer|\Z)", lower_text, re.DOTALL)

    req_text = req_section_match.group(1) if req_section_match else lower_text
    pref_text = pref_section_match.group(1) if pref_section_match else ""

    matched_skills_req = []
    matched_skills_pref = []

    for skill in COMMON_TECH_SKILLS:
        skill_re = r"\b" + re.escape(skill) + r"\b"
        if pref_text and re.search(skill_re, pref_text):
            if skill not in matched_skills_pref and skill not in matched_skills_req:
                matched_skills_pref.append(skill)
        elif re.search(skill_re, req_text):
            if skill not in matched_skills_req:
                matched_skills_req.append(skill)
        elif re.search(skill_re, lower_text):
            if skill not in matched_skills_req and skill not in matched_skills_pref:
                matched_skills_req.append(skill)

    # If no skills matched via dictionary, extract bullet points
    if not matched_skills_req:
        matched_skills_req = ["python", "machine learning", "data structures", "system design"]

    # 4. Detect Target Locations & Relocation
    target_locations = []
    for loc in ["pune", "noida", "bangalore", "bengaluru", "delhi", "gurgaon", "hyderabad", "mumbai", "chennai", "remote"]:
        if loc in lower_text:
            target_locations.append(loc.title())

    # 5. Detect Disqualifiers / Negative Indicators
    disqualifiers = []
    if any(term in lower_text for term in ["no consulting", "product company only", "consulting disqualifier", "tcs", "infosys"]):
        disqualifiers.append("Pure IT consulting background excluded")
    if any(term in lower_text for term in ["production experience required", "must have shipped to production", "no pure academic"]):
        disqualifiers.append("Pure academic/research with zero production deployment excluded")
    if any(term in lower_text for term in ["no langchain only", "beyond simple api calling", "prompt engineering only"]):
        disqualifiers.append("Surface-level API wrapper only experience excluded")

    # 6. Create clean semantic query string for embedding comparison
    query_parts = [
        f"Title: {title}",
        f"Experience: {exp_label}",
        f"Required Competencies: {', '.join(s.title() for s in matched_skills_req[:12])}",
        f"Preferred Competencies: {', '.join(s.title() for s in matched_skills_pref[:8])}"
    ]
    semantic_query = "\n".join(query_parts)

    return {
        "title": title,
        "experience_min": min_exp,
        "experience_max": max_exp,
        "experience_preferred": exp_label,
        "required_competencies": [s.title() for s in matched_skills_req],
        "preferred_competencies": [s.title() for s in matched_skills_pref],
        "target_locations": target_locations or ["India / Open to Relocation"],
        "disqualifiers": disqualifiers or [
            "Pure consulting company background without product experience",
            "Pure research/academic without production systems",
            "Profile without core matching skills"
        ],
        "semantic_query": semantic_query,
        "raw_text_snippet": text[:800] + ("..." if len(text) > 800 else "")
    }

def parse_jd(file_or_path: Union[str, BinaryIO, bytes], output_json_path: str = None, filename: str = "") -> Dict[str, Any]:
    """
    Main entry point: parses JD from file path, bytes, or file stream,
    and optionally writes parsed analysis to output_json_path.
    """
    raw_text = extract_text_from_file(file_or_path, filename=filename)
    analysis = parse_jd_content(raw_text, source_name=filename or "Job Description")

    if output_json_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_json_path)), exist_ok=True)
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"JD Analysis written to {output_json_path}")

    return analysis
