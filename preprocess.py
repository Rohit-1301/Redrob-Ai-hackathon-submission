import os
import sys
import json

# Add src to python path to import our custom honeypot logic
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from utils.score_candidates import check_honeypot

def main():
    input_file = os.path.join("data", "cleaned_candidates.jsonl")
    valid_file = os.path.join("data", "valid_candidates.jsonl")
    invalid_file = os.path.join("data", "invalid_candidates.jsonl")
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found! Run the directory cleanup and folder layout setup first.")
        return
        
    print(f"Starting candidate preprocessing on {input_file}...")
    total_count = 0
    valid_count = 0
    invalid_count = 0
    
    # Reason tracking
    reasons = {}
    
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(valid_file, "w", encoding="utf-8") as valfile, \
         open(invalid_file, "w", encoding="utf-8") as invfile:
         
        for line in infile:
            if not line.strip():
                continue
            
            total_count += 1
            candidate = json.loads(line)
            
            is_honeypot, reason = check_honeypot(candidate)
            
            if is_honeypot:
                invalid_count += 1
                invfile.write(line)
                
                # Standardize reason for grouping
                group_reason = "Unknown"
                if "Expert skill" in reason:
                    group_reason = "Expert Skill with 0 Duration"
                elif "Job duration mismatch" in reason:
                    group_reason = "Job Duration Calendar Violation"
                elif "Started at" in reason:
                    group_reason = "Startup Founding Year Violation (Started before company existed)"
                elif "exceeds company age" in reason:
                    group_reason = "Startup Founding Year Violation (Stated duration exceeds company age)"
                
                reasons[group_reason] = reasons.get(group_reason, 0) + 1
            else:
                valid_count += 1
                valfile.write(line)
                
    print("\n--- Preprocessing Results ---")
    print(f"Total Candidates:  {total_count}")
    print(f"Valid Candidates:  {valid_count} ({valid_count / total_count * 100:.2f}%)")
    print(f"Invalid (Honeypot): {invalid_count} ({invalid_count / total_count * 100:.2f}%)")
    
    print("\nHoneypot Reason Breakdown:")
    for reason, count in reasons.items():
        print(f" - {reason}: {count} candidates")
        
    print(f"\nFiles generated successfully:")
    print(f" - Valid: {valid_file}")
    print(f" - Invalid: {invalid_file}")

if __name__ == "__main__":
    main()
