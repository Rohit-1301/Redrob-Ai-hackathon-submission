import datetime

# Reference date for the pipeline checks (current state is June 2026)
REFERENCE_DATE = datetime.date(2026, 6, 20)

# Consulting and IT services giants (for pure consulting disqualifier)
CONSULTING_COMPANIES = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "mindtree", "wipro limited", "infosys limited", 
    "tata consultancy", "cognizant technology solutions", "accenture services"
}

# Target Indian hubs and regions
TARGET_LOCATIONS = {
    "noida", "pune", "ncr", "delhi", "gurgaon", "mumbai", "hyderabad", 
    "bangalore", "bengaluru", "ghaziabad", "faridabad"
}

# Core AI/ML/IR keywords for skills and JD matching
AI_ML_KEYWORDS = {
    "embeddings", "vector database", "hybrid search", "pinecone", "weaviate", 
    "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "ndcg", "mrr", 
    "map", "evaluation frameworks", "lora", "qlora", "peft", "fine-tuning", 
    "learning-to-rank", "xgboost", "neural ranking", "reranking", "llm", "nlp", 
    "retrieval", "search system", "recommendation", "dense retrieval", "rag",
    "retrieval-augmented generation", "machine learning", "deep learning", 
    "pytorch", "tensorflow", "scikit-learn"
}

# Target JD mandatory/preferred skill names (lowercased)
JD_REQUIRED_SKILLS = {
    "embeddings", "vector databases", "vector database", "hybrid search", 
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", 
    "faiss", "ndcg", "mrr", "map", "evaluation", "python"
}

JD_PREFERRED_SKILLS = {
    "lora", "qlora", "peft", "fine-tuning", "learning-to-rank", "xgboost", 
    "reranking", "distributed systems", "inference optimization"
}

# Keywords to detect computer vision / speech only background
CV_SPEECH_KEYWORDS = {
    "computer vision", "object detection", "yolo", "segmentation", "opencv", 
    "speech recognition", "tts", "asr", "whisper", "speech-to-text", "text-to-speech",
    "robotics", "ros", "lidar"
}
