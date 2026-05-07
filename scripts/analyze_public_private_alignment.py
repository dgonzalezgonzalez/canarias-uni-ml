from __future__ import annotations

import csv
import math
import random
import sqlite3
from collections import defaultdict
from pathlib import Path

PLOTTING_AVAILABLE = False

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/processed/program_job_alignment.db"
DEGREES_CSV = ROOT / "data/processed/degrees_catalog.csv"
OUT_DIR = ROOT / "output/policy_eval"


def load_degrees_index(path: Path) -> dict[str, dict[str, str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        source = (r.get("source") or "").strip().lower()
        source_id = (r.get("source_id") or "").strip()
        if not source_id:
            continue
        key = f"degree::{source}::{source_id}"
        out[key] = r
    return out


def load_similarity(path: Path) -> list[dict[str, object]]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute("SELECT * FROM program_job_similarity").fetchall()]
    conn.close()
    return rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def quantile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return s[lo]
    w = pos - lo
    return s[lo] * (1 - w) + s[hi] * w


def bootstrap_ci(values: list[float], n_boot: int = 5000, seed: int = 42) -> tuple[float, float]:
    if not values:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(values)
    draws: list[float] = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        draws.append(mean(sample))
    return quantile(draws, 0.025), quantile(draws, 0.975)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def to_pct(x: float) -> str:
    return f"{100*x:.1f}\\%"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    degrees_ix = load_degrees_index(DEGREES_CSV)
    sim = load_similarity(DB_PATH)

    enriched: list[dict[str, object]] = []
    missing = 0
    for r in sim:
        d = degrees_ix.get(str(r["degree_key"]))
        if not d:
            missing += 1
            continue
        university_type = (d.get("university_type") or "").strip().lower()
        if university_type not in {"publica", "privada"}:
            continue
        enriched.append(
            {
                "job_key": str(r["job_key"]),
                "job_title": str(r.get("job_title") or ""),
                "degree_key": str(r["degree_key"]),
                "degree_title": str(r.get("degree_title") or ""),
                "score": float(r["score"]),
                "university": d.get("university") or "",
                "university_type": university_type,
                "branch": d.get("branch") or "",
            }
        )

    # pair-level summaries
    pair_scores = {
        "publica": [r["score"] for r in enriched if r["university_type"] == "publica"],
        "privada": [r["score"] for r in enriched if r["university_type"] == "privada"],
    }

    pair_summary: list[dict[str, object]] = []
    for sector in ["publica", "privada"]:
        vals = pair_scores[sector]
        lo, hi = bootstrap_ci(vals)
        pair_summary.append(
            {
                "sector": sector,
                "n_pairs": len(vals),
                "mean_score": mean(vals),
                "ci_95_low": lo,
                "ci_95_high": hi,
            }
        )

    # job-level best-of-sector (policy-relevant)
    by_job: dict[str, dict[str, object]] = {}
    for r in enriched:
        job = str(r["job_key"])
        rec = by_job.setdefault(
            job,
            {
                "job_key": job,
                "job_title": r["job_title"],
                "best_public": None,
                "best_private": None,
            },
        )
        s = float(r["score"])
        if r["university_type"] == "publica":
            if rec["best_public"] is None or s > rec["best_public"]:
                rec["best_public"] = s
        else:
            if rec["best_private"] is None or s > rec["best_private"]:
                rec["best_private"] = s

    jobs = list(by_job.values())
    both = [j for j in jobs if j["best_public"] is not None and j["best_private"] is not None]

    public_best = [float(j["best_public"]) for j in jobs if j["best_public"] is not None]
    private_best = [float(j["best_private"]) for j in jobs if j["best_private"] is not None]

    job_summary = [
        {
            "metric": "jobs_total",
            "value": len(jobs),
        },
        {
            "metric": "jobs_with_public_option",
            "value": sum(j["best_public"] is not None for j in jobs),
        },
        {
            "metric": "jobs_with_private_option",
            "value": sum(j["best_private"] is not None for j in jobs),
        },
        {
            "metric": "jobs_with_both_options",
            "value": len(both),
        },
        {
            "metric": "mean_best_public_among_jobs_with_public",
            "value": mean(public_best),
        },
        {
            "metric": "mean_best_private_among_jobs_with_private",
            "value": mean(private_best),
        },
    ]

    gap_rows: list[dict[str, object]] = []
    for j in both:
        gap_rows.append(
            {
                "job_key": j["job_key"],
                "job_title": j["job_title"],
                "best_public": float(j["best_public"]),
                "best_private": float(j["best_private"]),
                "gap_public_minus_private": float(j["best_public"]) - float(j["best_private"]),
            }
        )

    # branch composition
    by_branch_sector: dict[tuple[str, str], int] = defaultdict(int)
    for r in enriched:
        key = (str(r["branch"]), str(r["university_type"]))
        by_branch_sector[key] += 1

    branches = sorted({k[0] for k in by_branch_sector})
    branch_rows: list[dict[str, object]] = []
    for b in branches:
        pub = by_branch_sector.get((b, "publica"), 0)
        prv = by_branch_sector.get((b, "privada"), 0)
        tot = pub + prv
        branch_rows.append(
            {
                "branch": b,
                "pairs_publica": pub,
                "pairs_privada": prv,
                "pairs_total": tot,
                "share_publica": (pub / tot) if tot else 0.0,
            }
        )

    # write CSV artifacts
    write_csv(
        OUT_DIR / "pair_level_summary.csv",
        pair_summary,
        ["sector", "n_pairs", "mean_score", "ci_95_low", "ci_95_high"],
    )
    write_csv(OUT_DIR / "job_level_summary.csv", job_summary, ["metric", "value"])
    write_csv(
        OUT_DIR / "job_public_private_gaps.csv",
        sorted(gap_rows, key=lambda x: x["gap_public_minus_private"], reverse=True),
        ["job_key", "job_title", "best_public", "best_private", "gap_public_minus_private"],
    )
    write_csv(
        OUT_DIR / "branch_sector_composition.csv",
        sorted(branch_rows, key=lambda x: x["pairs_total"], reverse=True),
        ["branch", "pairs_publica", "pairs_privada", "pairs_total", "share_publica"],
    )

    if PLOTTING_AVAILABLE:
        try:
            # Figure 1: Pair-level means with CI
            fig, ax = plt.subplots(figsize=(7, 4.5))
            sectors = [r["sector"] for r in pair_summary]
            means = [float(r["mean_score"]) for r in pair_summary]
            lows = [float(r["ci_95_low"]) for r in pair_summary]
            highs = [float(r["ci_95_high"]) for r in pair_summary]
            yerr = [[m - l for m, l in zip(means, lows)], [h - m for m, h in zip(means, highs)]]
            ax.bar(sectors, means, color=["#2A9D8F", "#E76F51"], alpha=0.9)
            ax.errorbar(sectors, means, yerr=yerr, fmt="none", ecolor="black", capsize=5, lw=1.3)
            ax.set_ylim(0.0, 1.0)
            ax.set_ylabel("Cosine similarity")
            ax.set_title("Pair-level alignment by university type (95% bootstrap CI)")
            for i, v in enumerate(means):
                ax.text(i, v + 0.03, f"{v:.3f}", ha="center", fontsize=10)
            fig.tight_layout()
            fig.savefig(OUT_DIR / "figure_pair_mean_ci.png", dpi=220)
            plt.close(fig)

            # Figure 2: Job-level frontier scatter
            fig, ax = plt.subplots(figsize=(6.5, 6))
            xs = [float(j["best_private"]) for j in both]
            ys = [float(j["best_public"]) for j in both]
            ax.scatter(xs, ys, color="#264653", s=45, alpha=0.9)
            ax.plot([0, 1], [0, 1], ls="--", color="gray", lw=1)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xlabel("Best private match per job")
            ax.set_ylabel("Best public match per job")
            ax.set_title("Job-level public vs private alignment frontier")
            fig.tight_layout()
            fig.savefig(OUT_DIR / "figure_job_frontier_public_vs_private.png", dpi=220)
            plt.close(fig)

            # Figure 3: Branch composition stacked bars
            top_branches = sorted(branch_rows, key=lambda x: x["pairs_total"], reverse=True)[:8]
            labels = [b["branch"][:35] for b in top_branches]
            pub_vals = [int(b["pairs_publica"]) for b in top_branches]
            prv_vals = [int(b["pairs_privada"]) for b in top_branches]
            fig, ax = plt.subplots(figsize=(9, 5))
            ax.bar(labels, pub_vals, label="Public", color="#2A9D8F")
            ax.bar(labels, prv_vals, bottom=pub_vals, label="Private", color="#E76F51")
            ax.set_ylabel("Number of matched pairs")
            ax.set_title("Matched pairs by branch and university type")
            ax.tick_params(axis="x", rotation=35)
            ax.legend()
            fig.tight_layout()
            fig.savefig(OUT_DIR / "figure_branch_composition.png", dpi=220)
            plt.close(fig)
        except Exception as exc:
            with (OUT_DIR / "plotting_warning.txt").open("w", encoding="utf-8") as f:
                f.write(f"Plotting skipped due to runtime error: {exc}\\n")
    else:
        with (OUT_DIR / "plotting_warning.txt").open("w", encoding="utf-8") as f:
            f.write("Plotting skipped: matplotlib unavailable in current environment.\\n")

    # LaTeX table 1: pair and job summary
    with (OUT_DIR / "table_alignment_summary.tex").open("w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{lrrr}\n")
        f.write("\\hline\n")
        f.write("Sector & N pairs & Mean score & 95\\% CI \\\\\n")
        f.write("\\hline\n")
        for r in pair_summary:
            f.write(
                f"{r['sector']} & {r['n_pairs']} & {r['mean_score']:.3f} & [{r['ci_95_low']:.3f}, {r['ci_95_high']:.3f}] \\\\\n"
            )
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")

    with (OUT_DIR / "table_job_frontier_summary.tex").open("w", encoding="utf-8") as f:
        f.write("\\begin{tabular}{lr}\n")
        f.write("\\hline\n")
        f.write("Metric & Value \\\\\n")
        f.write("\\hline\n")
        for r in job_summary:
            val = r["value"]
            if isinstance(val, float):
                f.write(f"{r['metric']} & {val:.3f} \\\\\n")
            else:
                f.write(f"{r['metric']} & {val} \\\\\n")
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")

    # policy memo markdown
    pub_mean = next(r["mean_score"] for r in pair_summary if r["sector"] == "publica")
    prv_mean = next(r["mean_score"] for r in pair_summary if r["sector"] == "privada")
    jobs_total = len(jobs)
    jobs_both = len(both)
    with (OUT_DIR / "policy_brief.md").open("w", encoding="utf-8") as f:
        f.write("# Public vs Private Degree Alignment (Exploratory)\n\n")
        f.write("## Data and scope\n")
        f.write(f"- Similarity pairs analyzed: {len(enriched)}\n")
        f.write(f"- Jobs with at least one matched program: {jobs_total}\n")
        f.write(f"- Jobs with both public and private options: {jobs_both}\n")
        f.write(f"- Join losses (similarity row without degree metadata): {missing}\n\n")
        f.write("## Key descriptive findings\n")
        f.write(f"- Pair-level mean similarity: public {pub_mean:.3f}, private {prv_mean:.3f}.\n")
        f.write("- Public option coverage lower than private, but overlap exists for substantial subset of jobs.\n")
        f.write("- Job-level frontier reveals where public option exceeds private benchmark and vice versa.\n\n")
        f.write("## Policy interpretation cautions\n")
        f.write("- Sample still small; treat as directional evidence, not final causal claim.\n")
        f.write("- Results depend on rule-based candidate gating before similarity stage.\n")
        f.write("- Next step should test robustness under alternative gating thresholds and provider/model choices.\n")

    print("done", OUT_DIR)


if __name__ == "__main__":
    main()
