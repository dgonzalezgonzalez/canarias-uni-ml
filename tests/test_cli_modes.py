from src.canarias_uni_ml.cli import build_parser


def test_cli_jobs_scrape_mode():
    parser = build_parser()
    args = parser.parse_args(["jobs", "scrape", "--limit-per-source", "10"])
    assert args.domain == "jobs"
    assert args.jobs_command == "scrape"
    assert args.limit_per_source == 10


def test_cli_embed_mode():
    parser = build_parser()
    args = parser.parse_args(["embed", "build", "--provider", "groq", "--dry-run"])
    assert args.domain == "embed"
    assert args.embed_command == "build"
    assert args.provider == "groq"
    assert args.dry_run is True
