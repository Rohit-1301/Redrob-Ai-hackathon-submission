def rank_candidates(scores):
    # Sort in descending order of score, breaking ties with candidate_id ascending
    # We use -x["score"] for descending float, and x["candidate_id"] for ascending string
    scores.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    return scores
