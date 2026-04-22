from __future__ import annotations

import argparse

from dotenv import load_dotenv

from .config import Settings
from .degrees.catalog import write_degree_catalog
from .embeddings.pipeline import run_embedding_pipeline
from .jobs.pipeline import run_jobs_pipeline, run_jobs_scale

load_dotenv()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="canarias-uni-ml pipelines")
    subparsers = parser.add_subparsers(dest="domain", required=True)

    jobs = subparsers.add_parser("jobs", help="Job scraping workflows")
    jobs_sub = jobs.add_subparsers(dest="jobs_command", required=True)
    jobs_scrape = jobs_sub.add_parser("scrape", help="Scrape jobs")
    jobs_scrape.add_argument("--limit-per-source", type=int, default=50)
    jobs_scrape.add_argument("--max-total", type=int)
    jobs_scrape.add_argument("--output")

    jobs_scale = jobs_sub.add_parser("scale", help="Scaled scraping run")
    jobs_scale.add_argument("--output")
    jobs_scale.add_argument("--time-limit", type=int, default=45)
    jobs_scale.add_argument("--max-total", type=int, default=40_000)
    jobs_scale.add_argument("--indeed-share", type=float, default=0.82)
    jobs_scale.add_argument("--sce-share", type=float, default=0.13)
    jobs_scale.add_argument("--turijobs-share", type=float, default=0.05)
    jobs_scale.add_argument("--sce-only", action="store_true")

    degrees = subparsers.add_parser("degrees", help="Degree catalog workflows")
    degrees_sub = degrees.add_subparsers(dest="degrees_command", required=True)
    degrees_catalog = degrees_sub.add_parser("catalog", help="Build degree catalog from fixtures or public sources")
    degrees_catalog.add_argument("--output")
    degrees_catalog.add_argument("--fixture")
    degrees_catalog.add_argument("--live-aneca", action="store_true")
    degrees_catalog.add_argument(
        "--cycles",
        default="grado,master,doctorado",
        help="Comma-separated title cycles (grado,master,doctorado)",
    )
    degrees_catalog.add_argument("--limit", type=int)
    degrees_catalog.add_argument("--max-pages", type=int)
    degrees_catalog.add_argument("--with-report-text", action="store_true")
    degrees_catalog.add_argument("--canary-only", action="store_true")
    degrees_catalog.add_argument("--resolve-university-memory", action="store_true")

    embed = subparsers.add_parser("embed", help="Embedding workflows")
    embed_sub = embed.add_subparsers(dest="embed_command", required=True)
    embed_build = embed_sub.add_parser("build", help="Build embedding manifest")
    embed_build.add_argument("--input")
    embed_build.add_argument("--output")
    embed_build.add_argument("--provider", choices=["openai", "groq"], default="openai")
    embed_build.add_argument("--model")
    embed_build.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()

    if args.domain == "jobs":
        if args.jobs_command == "scrape":
            return run_jobs_pipeline(
                limit_per_source=args.limit_per_source,
                output_path=args.output or str(settings.jobs_output),
                max_total=args.max_total,
            )
        if args.jobs_command == "scale":
            return run_jobs_scale(
                output_path=args.output or str(settings.jobs_output),
                time_limit_minutes=args.time_limit,
                max_total=args.max_total,
                indeed_share=args.indeed_share,
                sce_share=args.sce_share,
                turijobs_share=args.turijobs_share,
                sce_only=args.sce_only,
            )

    if args.domain == "degrees" and args.degrees_command == "catalog":
        cycles = tuple(x.strip().lower() for x in args.cycles.split(",") if x.strip())
        return write_degree_catalog(
            output_path=args.output or str(settings.degrees_catalog_output),
            fixture_path=args.fixture,
            live_aneca=args.live_aneca,
            cycles=cycles,
            limit=args.limit,
            max_pages=args.max_pages,
            with_report_text=args.with_report_text,
            canary_only=args.canary_only,
            resolve_university_memory=args.resolve_university_memory,
            db_path=str(settings.degrees_db_output),
        )

    if args.domain == "embed" and args.embed_command == "build":
        return run_embedding_pipeline(
            input_path=args.input or str(settings.corpus_output),
            output_path=args.output or str(settings.embeddings_manifest_output),
            provider_name=args.provider,
            model=args.model,
            dry_run=args.dry_run,
            settings=settings,
        )

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
