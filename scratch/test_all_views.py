import os
import sys
import json
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

# Set paths
project_root = r"c:\Users\rg975\OneDrive\Documents\Rohit's programming\python projects\Redrob-Ai-hackathon-submission"
app_root = os.path.join(project_root, "SelectedCandidates")

# Load data
csv_baseline = os.path.join(app_root, "outputs/top_100_candidates.csv")
exp_baseline = os.path.join(app_root, "outputs/top_100_explanations.json")

df_b = pd.read_csv(csv_baseline)
with open(exp_baseline, "r", encoding="utf-8") as f:
    exp_b = json.load(f)
exp_map = {item["candidate_id"]: item for item in exp_b}

names, titles, comps, locs, exps, skills_c, rrs = [], [], [], [], [], [], []
for cid in df_b["candidate_id"]:
    e = exp_map.get(cid, {})
    ph = e.get("profile_highlights", {})
    stren = e.get("strengths", {})
    names.append(ph.get("name", "Unknown"))
    titles.append(ph.get("current_title", "Software Engineer"))
    comps.append(ph.get("current_company", "Tech Corp"))
    locs.append(ph.get("location", "India"))
    exps.append(float(stren.get("experience_years", 6.0)))
    skills_c.append(len(stren.get("matched_required_skills", [])) + len(stren.get("matched_preferred_skills", [])))
    rrs.append(float(stren.get("recruiter_response_rate", 0.5)))
    
df_b["name"] = names
df_b["title"] = titles
df_b["company"] = comps
df_b["location"] = locs
df_b["experience"] = exps
df_b["skills"] = skills_c
df_b["response_rate"] = rrs

DARK_BG = "#0B1120"
CARD_BG = "#1E293B"
BLUE = "#38BDF8"
PURPLE = "#818CF8"
TEAL = "#34D399"
AMBER = "#FBBF24"
RED = "#F87171"
GREEN = "#4ADE80"

def set_dark_figure(fig, ax_or_axes):
    fig.patch.set_facecolor(DARK_BG)
    axes = [ax_or_axes] if not isinstance(ax_or_axes, (list, np.ndarray)) else ax_or_axes
    for ax in np.ravel(axes):
        ax.set_facecolor(CARD_BG)
        ax.tick_params(colors="#CBD5E1", labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor((1.0, 1.0, 1.0, 0.08))
            spine.set_linewidth(0.6)
    return fig, axes

for cohort_size in [10, 50, 100]:
    print(f"\n================ TESTING COHORT SIZE: {cohort_size} ================")
    cohort_n = min(cohort_size, len(df_b))
    df = df_b.head(cohort_n).copy()
    all_explanations = exp_b
    exp_dict = exp_map

    # Test Page 1: Overview
    try:
        score_bins = pd.cut(df["score"], bins=5)
        band_counts = score_bins.value_counts().sort_index()
        fig, ax = plt.subplots(figsize=(10, 3.2))
        set_dark_figure(fig, ax)
        bars = ax.bar([f"{b.left:.2f}–{b.right:.2f}" for b in band_counts.index], band_counts.values, width=0.55)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, str(int(bar.get_height())))
        plt.close(fig)
        print("  Page 1 (Overview & KPIs): SUCCESS")
    except Exception as e:
        print(f"  Page 1 (Overview & KPIs): FAILED -> {e}")

    # Test Page 2: Data Analysis
    try:
        fig, ax = plt.subplots(figsize=(6, 4))
        set_dark_figure(fig, ax)
        n, bins, patches = ax.hist(df["score"], bins=12)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        set_dark_figure(fig, ax)
        exp_bins = pd.cut(df["experience"], bins=[0, 4, 6, 8, 10, 20], labels=["<4y", "4–6y", "6–8y", "8–10y", "10y+"])
        exp_counts = exp_bins.value_counts().sort_index()
        ax.pie(exp_counts.values, labels=exp_counts.index)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        set_dark_figure(fig, ax)
        rr_bins = pd.cut(df["response_rate"], bins=[0, 0.3, 0.5, 0.7, 0.9, 1.01], labels=["<30%", "30–50%", "50–70%", "70–90%", ">90%"])
        rr_counts = rr_bins.value_counts().sort_index()
        bars = ax.bar(rr_counts.index.astype(str), rr_counts.values)
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.2, str(int(bar.get_height())))
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 4))
        set_dark_figure(fig, ax)
        ax.plot(df["rank"], df["score"])
        ax.fill_between(df["rank"], df["score"], df["score"].min() - 0.005)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(11, 4.2))
        set_dark_figure(fig, ax)
        sc = ax.scatter(df["experience"], df["score"], c=df["skills"])
        plt.colorbar(sc, ax=ax)
        plt.close(fig)
        print("  Page 2 (Data Analysis): SUCCESS")
    except Exception as e:
        print(f"  Page 2 (Data Analysis): FAILED -> {e}")

    # Test Page 3: Location Insights
    try:
        loc_counts = df["location"].value_counts()
        fig, ax = plt.subplots(figsize=(8, max(4.5, len(loc_counts) * 0.45)))
        set_dark_figure(fig, ax)
        bars = ax.barh(loc_counts.index[::-1], loc_counts.values[::-1], height=0.65)
        plt.close(fig)

        top_locs = loc_counts.head(6)
        others = loc_counts.iloc[6:].sum()
        pie_data = pd.concat([top_locs, pd.Series({"Others": others})]) if others > 0 else top_locs
        fig, ax = plt.subplots(figsize=(6, 5))
        set_dark_figure(fig, ax)
        ax.pie(pie_data.values, labels=pie_data.index)
        plt.close(fig)
        print("  Page 3 (Location Insights): SUCCESS")
    except Exception as e:
        print(f"  Page 3 (Location Insights): FAILED -> {e}")

    # Test Page 4: Role & Experience
    try:
        role_counts = df["title"].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(7, max(4, len(role_counts) * 0.45)))
        set_dark_figure(fig, ax)
        bars = ax.barh(role_counts.index[::-1], role_counts.values[::-1])
        plt.close(fig)

        role_scores = df.groupby("title")["score"].mean().loc[role_counts.index].sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(7, max(4, len(role_scores) * 0.45)))
        set_dark_figure(fig, ax)
        bars2 = ax.barh(role_scores.index[::-1], role_scores.values[::-1])
        ax.set_xlim(df["score"].min() - 0.02, df["score"].max() + 0.02)
        plt.close(fig)

        df_exp = df.copy()
        df_exp["tier"] = pd.cut(df_exp["experience"], bins=[0, 4, 6, 8, 20], labels=["Junior (<=4y)", "Mid-Level (4-6y)", "Senior (6-8y)", "Lead/Staff (8y+)"])
        exp_summary = df_exp.groupby("tier", observed=False).agg(
            Count=("candidate_id", "count"),
            Avg_Score=("score", lambda x: round(x.mean(), 4)),
            Avg_Skills=("skills", lambda x: round(x.mean(), 1))
        ).reset_index()
        print("  Page 4 (Role & Experience): SUCCESS")
    except Exception as e:
        print(f"  Page 4 (Role & Experience): FAILED -> {e}")

    # Test Page 5: Skills Intelligence
    try:
        req_skills_all, pref_skills_all = [], []
        for cid in df["candidate_id"]:
            item = exp_dict.get(cid, {})
            s = item.get("strengths", {})
            req_skills_all.extend(s.get("matched_required_skills", []))
            pref_skills_all.extend(s.get("matched_preferred_skills", []))
        req_counter = Counter(req_skills_all)
        pref_counter = Counter(pref_skills_all)
        top_req = pd.DataFrame(req_counter.most_common(12), columns=["Skill", "Count"])
        top_pref = pd.DataFrame(pref_counter.most_common(12), columns=["Skill", "Count"])
        print("  Page 5 (Skills Intelligence): SUCCESS")
    except Exception as e:
        print(f"  Page 5 (Skills Intelligence): FAILED -> {e}")

    # Test Page 6: Company Insights
    try:
        comp_counts = df["company"].value_counts().head(12)
        fig, ax = plt.subplots(figsize=(8, max(4.5, len(comp_counts) * 0.45)))
        set_dark_figure(fig, ax)
        bars = ax.barh(comp_counts.index[::-1], comp_counts.values[::-1])
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 5))
        set_dark_figure(fig, ax)
        ax.pie(comp_counts.head(7).values, labels=comp_counts.head(7).index)
        plt.close(fig)
        print("  Page 6 (Company Insights): SUCCESS")
    except Exception as e:
        print(f"  Page 6 (Company Insights): FAILED -> {e}")

    # Test Page 8: Candidate Deep Dive
    try:
        candidate_options = [f"Rank #{row['rank']} · {row['name']} ({row['candidate_id']}) — Score: {row['score']:.4f}" for _, row in df.iterrows()]
        # Test inspecting EVERY candidate in cohort
        for opt in candidate_options:
            selected_cid = re.search(r"\((CAND_\d+)\)", opt).group(1)
            item = exp_dict[selected_cid]
            cand_row = df[df["candidate_id"] == selected_cid].iloc[0]
        print("  Page 8 (Candidate Deep-Dive): SUCCESS")
    except Exception as e:
        print(f"  Page 8 (Candidate Deep-Dive): FAILED -> {e}")

    # Test Page 9: Full Table
    try:
        min_score = float(df["score"].min())
        max_score = float(df["score"].max())
        assert min_score <= max_score
        fdf = df[df["score"] >= min_score].copy()
        print("  Page 9 (Full Table): SUCCESS")
    except Exception as e:
        print(f"  Page 9 (Full Table): FAILED -> {e}")
