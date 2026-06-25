from utils.get_candidates import get_candidates
from utils.score_candidates import score_candidate
from utils.rank_candidates import rank_candidates
from jd.senion_ai_engineer import senior_ai_enginerr_jd
from utils.recommend_candidates import recommend_candidate


def main():
    candidates = get_candidates()
    jd = senior_ai_enginerr_jd()

    scores = score_candidate(candidates, jd)
    ranks = rank_candidates(scores)
    recommend_candidates = recommend_candidate(ranks)

    print("Scores:", scores[:5])
    print("Ranks:", ranks[:5])
    print("Recommended Candidates:", recommend_candidates)



if __name__ == "__main__":
    main()
