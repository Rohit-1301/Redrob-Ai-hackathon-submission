import os
import sys
import csv
import json
from datetime import datetime

# Add src/ to Python search path so we can import our core modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))
from utils.score_candidates import check_honeypot

def load_candidates_db():
    candidates = {}
    db_paths = [
        os.path.join("data", "candidates.jsonl"),
        os.path.join("data", "cleaned_candidates.jsonl"),
        "candidates.jsonl",
        "cleaned_candidates.jsonl"
    ]
    
    selected_path = None
    for path in db_paths:
        if os.path.exists(path):
            selected_path = path
            break
            
    if not selected_path:
        print("Error: Candidate database file (candidates.jsonl) not found in data/ or root!")
        return None
        
    print(f"Loading candidate database from {selected_path}...")
    try:
        with open(selected_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if not line.strip():
                    continue
                c = json.loads(line)
                candidates[c["candidate_id"]] = c
        print(f"Successfully loaded {len(candidates)} candidates.")
        return candidates
    except Exception as e:
        print(f"Error loading candidate database: {e}")
        return None

def clean_row_keys(row):
    """Gracefully handle BOM and whitespace in CSV row keys."""
    cleaned = {}
    for k, v in row.items():
        if k is None:
            continue
        # Strip Byte Order Mark (BOM) and whitespace
        k_clean = k.encode('utf-8').decode('utf-8-sig').strip().lower()
        cleaned[k_clean] = v.strip() if v else ""
    return cleaned

def check_submission_file(file_path, db):
    file_name = os.path.basename(file_path)
    print(f"\nAnalyzing submission file: {file_name}...")
    
    results = {
        "file_name": file_name,
        "format_ok": True,
        "format_errors": [],
        "total_rows": 0,
        "valid_count": 0,
        "honeypot_count": 0,
        "unregistered_count": 0,
        "honeypots": [],
        "unregistered": []
    }
    
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            # Check if file is empty
            first_char = f.read(1)
            if not first_char:
                results["format_ok"] = False
                results["format_errors"].append("File is empty.")
                return results
            f.seek(0)
            
            reader = csv.DictReader(f)
            
            # Field names validation
            fieldnames = [fn.encode('utf-8').decode('utf-8-sig').strip().lower() for fn in (reader.fieldnames or [])]
            required_cols = ["candidate_id", "rank", "score", "reasoning"]
            missing_cols = [col for col in required_cols if col not in fieldnames]
            
            if missing_cols:
                results["format_ok"] = False
                results["format_errors"].append(f"Missing required column(s): {', '.join(missing_cols)}")
                
            # Process rows
            for idx, raw_row in enumerate(reader):
                results["total_rows"] += 1
                row = clean_row_keys(raw_row)
                cid = row.get("candidate_id")
                rank = row.get("rank")
                score = row.get("score")
                reasoning = row.get("reasoning")
                
                # Basic row checks
                if not cid:
                    results["format_errors"].append(f"Row {idx+2}: Missing candidate_id.")
                    results["format_ok"] = False
                    continue
                    
                if cid not in db:
                    results["unregistered_count"] += 1
                    results["unregistered"].append({
                        "candidate_id": cid,
                        "rank": rank or str(idx+1),
                        "score": score or "N/A"
                    })
                    continue
                    
                # Honeypot checks
                cand = db[cid]
                is_honeypot, reason = check_honeypot(cand)
                
                profile = cand.get("profile", {})
                cand_name = profile.get("anonymized_name", "Unknown")
                cand_title = profile.get("current_title") or profile.get("headline") or "Unknown Title"
                
                row_data = {
                    "candidate_id": cid,
                    "name": cand_name,
                    "title": cand_title,
                    "rank": rank or str(idx+1),
                    "score": score or "N/A",
                    "reasoning": reasoning or ""
                }
                
                if is_honeypot:
                    results["honeypot_count"] += 1
                    row_data["honeypot_reason"] = reason
                    results["honeypots"].append(row_data)
                else:
                    results["valid_count"] += 1
                    
        # Check row count
        if results["total_rows"] != 100:
            results["format_errors"].append(f"Expected exactly 100 data rows, found {results['total_rows']}.")
            results["format_ok"] = False
            
    except Exception as e:
        results["format_ok"] = False
        results["format_errors"].append(f"Failed to read file: {e}")
        
    return results

def generate_report(file_results):
    report_path = os.path.join("checker", "report.md")
    print(f"\nGenerating Markdown report: {report_path}...")
    
    md = []
    md.append("# Candidate Submission Validation & Honeypot Analysis Report")
    md.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    md.append("\nThis report validates submitted competitor ranking `.csv` files against formatting requirements and audits them for synthetic honeypot trap profiles.")
    
    # ----------------------------------------------------
    # 1. Summary Comparison Table
    # ----------------------------------------------------
    md.append("\n## 1. High-Level Submissions Summary\n")
    md.append("| Submission File | Total Rows | Valid Candidates | Honeypots Found | Honeypot Rate % | Format Check | Status |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    
    for r in file_results:
        rate = (r["honeypot_count"] / r["total_rows"]) * 100 if r["total_rows"] > 0 else 0.0
        status_banner = "✅ PASSED"
        
        # Disqualified if rate > 10% or format issues present
        if not r["format_ok"] or rate > 10.0 or r["unregistered_count"] > 0:
            status_banner = "❌ DISQUALIFIED"
            
        fmt_status = "✅ OK" if r["format_ok"] else "❌ ERRORS"
        
        md.append(f"| {r['file_name']} | {r['total_rows']} | {r['valid_count']} | {r['honeypot_count']} | {rate:.1f}% | {fmt_status} | {status_banner} |")
        
    # ----------------------------------------------------
    # 2. Detailed Findings per File
    # ----------------------------------------------------
    md.append("\n---\n")
    md.append("## 2. Detailed Diagnostics per Submission")
    
    for r in file_results:
        rate = (r["honeypot_count"] / r["total_rows"]) * 100 if r["total_rows"] > 0 else 0.0
        md.append(f"\n### File: `{r['file_name']}`")
        
        # Status Card
        if not r["format_ok"]:
            md.append("> [!CAUTION]")
            md.append("> **Status: DISQUALIFIED** (Format Check Failed)")
            for err in r["format_errors"]:
                md.append(f"> - *Format Error:* {err}")
        elif rate > 10.0:
            md.append("> [!WARNING]")
            md.append(f"> **Status: DISQUALIFIED** (Honeypot Rate: **{rate:.1f}%** exceeds the 10.0% limit)")
            md.append(f"> - Total honeypots flagged: {r['honeypot_count']} in top {r['total_rows']}.")
        elif r["unregistered_count"] > 0:
            md.append("> [!CAUTION]")
            md.append(f"> **Status: DISQUALIFIED** (Contains {r['unregistered_count']} unregistered candidate IDs not in the database)")
        else:
            md.append("> [!NOTE]")
            md.append(f"> **Status: PASSED** (Honeypot Rate: **{rate:.1f}%** is within the allowed limit)")
            md.append("> - Format is valid. 0% honeypot presence. Fully compliant.")
            
        # Summary numbers
        md.append("\n**Submissions breakdown:**")
        md.append(f"- Stated rows: `{r['total_rows']}`")
        md.append(f"- Valid candidates: `{r['valid_count']}`")
        md.append(f"- Traps/Honeypots: `{r['honeypot_count']}`")
        md.append(f"- Unregistered candidate IDs: `{r['unregistered_count']}`")
        
        # Flagged Honeypots List
        if r["honeypots"]:
            md.append("\n**Flagged Honeypots details:**\n")
            md.append("| Rank | Candidate ID | Candidate Name | Current Title | Honeypot Reason |")
            md.append("| :---: | :---: | :--- | :--- | :--- |")
            for h in r["honeypots"]:
                md.append(f"| {h['rank']} | `{h['candidate_id']}` | {h['name']} | {h['title']} | {h['honeypot_reason']} |")
        else:
            md.append("\n🎉 **No honeypot profiles found in this submission.**")
            
        # Unregistered Candidates List
        if r["unregistered"]:
            md.append("\n⚠️ **Flagged Unregistered Candidate IDs:**\n")
            md.append("| Rank | Stated Candidate ID | Score |")
            md.append("| :---: | :---: | :---: |")
            for u in r["unregistered"]:
                md.append(f"| {u['rank']} | `{u['candidate_id']}` | {u['score']} |")
                
        md.append("\n---")
        
    # Write report file
    try:
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write("\n".join(md))
        print(f"Report written successfully to {report_path}")
    except Exception as e:
        print(f"Error writing Markdown report: {e}")

def main():
    db = load_candidates_db()
    if not db:
        return
        
    checker_dir = "checker"
    csv_files = [
        os.path.join(checker_dir, f)
        for f in os.listdir(checker_dir)
        if f.endswith('.csv')
    ]
    
    if not csv_files:
        print("\nNo submission CSV files found inside the 'checker/' directory.")
        print("Please place competitor .csv files inside the 'checker/' folder and run this script again.")
        return
        
    print(f"\nFound {len(csv_files)} submission files to analyze.")
    
    file_results = []
    for filepath in csv_files:
        res = check_submission_file(filepath, db)
        file_results.append(res)
        
    # Generate report
    generate_report(file_results)

if __name__ == "__main__":
    main()
