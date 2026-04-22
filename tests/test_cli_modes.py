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


def test_cli_degrees_live_aneca_mode():
    parser = build_parser()
    args = parser.parse_args(["degrees", "catalog", "--live-aneca", "--limit", "5", "--with-report-text"])
    assert args.domain == "degrees"
    assert args.degrees_command == "catalog"
    assert args.live_aneca is True
    assert args.limit == 5
    assert args.with_report_text is True
