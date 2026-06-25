import json
import numpy as np
import time
import os
import torch
from sentence_transformers import SentenceTransformer

def main():
    start_time = time.time()
    input_file = "data/cleaned_candidates.jsonl" if os.path.exists("data/cleaned_candidates.jsonl") else "cleaned_candidates.jsonl"
    output_file = "data/embeddings.npz" if os.path.exists("data") else "embeddings.npz"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
        
    print(f"Loading SentenceTransformer model 'all-MiniLM-L6-v2'...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
    
    print("Reading candidates and preparing headlines for embedding...")
    candidate_ids = []
    texts = []
    
    with open(input_file, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if not line.strip():
                continue
            c = json.loads(line)
            cid = c.get("candidate_id")
            profile = c.get("profile", {})
            headline = profile.get("headline", "")
            
            candidate_ids.append(cid)
            texts.append(headline)
            
    total_candidates = len(candidate_ids)
    print(f"Loaded {total_candidates} candidate headlines. Starting encoding...")
    
    # Run encoding
    # We use a batch size of 512 for optimal throughput
    embeddings = model.encode(texts, batch_size=512, show_progress_bar=True, convert_to_numpy=True)
    
    print(f"Finished encoding. Embedding shape: {embeddings.shape}")
    print(f"Saving to compressed numpy archive '{output_file}'...")
    
    # Save to compressed file
    np.savez_compressed(output_file, ids=np.array(candidate_ids), vectors=embeddings)
    
    elapsed = time.time() - start_time
    print(f"Successfully saved embeddings in {elapsed:.1f} seconds.")

if __name__ == "__main__":
    main()
