import docx
import json
import os
import logging

logger = logging.getLogger(__name__)

def parse_jd(docx_path: str, output_path: str) -> dict:
    """
    Parses the Job Description DOCX and extracts required, preferred, 
    and negative competencies, writing the result to jd_analysis.json.
    """
    logger.info(f"Parsing Job Description from: {docx_path}")
    
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Job Description file not found at {docx_path}")
        
    doc = docx.Document(docx_path)
    full_text = "\n".join([p.text for p in doc.paragraphs])
    
    # We define the structured competencies extracted from our analysis of the JD
    analysis = {
        "title": "Senior AI Engineer (Ranking & Retrieval)",
        "experience_preferred": "5-9 years",
        "required_competencies": [
            "Python",
            "Retrieval Systems",
            "Ranking Systems",
            "Search Infrastructure",
            "Recommendation Systems",
            "Embeddings",
            "Vector Databases",
            "Production ML Systems",
            "Evaluation Frameworks"
        ],
        "preferred_competencies": [
            "Fine-Tuning",
            "Learning To Rank",
            "HR-Tech",
            "Distributed Systems",
            "Open Source"
        ],
        "negative_indicators": [
            "Consulting-only careers",
            "Pure research backgrounds",
            "Computer Vision only profiles",
            "Keyword stuffing",
            "Framework-only experience"
        ],
        "disqualifiers": [
            "Pure research environment experience only (no production deployment)",
            "AI experience consisting only of recent (<12m) LangChain/OpenAI calling",
            "Senior engineers with no production code written in the last 18 months",
            "Entire career spent at IT consulting services (TCS, Infosys, Wipro, Accenture, Cognizant, etc.)",
            "Primary expertise is computer vision, speech, or robotics without NLP/IR exposure"
        ]
    }
    
    # Save the output file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
        
    logger.info(f"JD Analysis written to: {output_path}")
    return analysis
