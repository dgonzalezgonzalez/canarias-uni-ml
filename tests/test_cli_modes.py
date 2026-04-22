from src.canarias_uni_ml.cli import build_parser


def test_cli_jobs_scrape_mode():
    parser = build_parser()
    args = parser.parse_args(["jobs", "scrape", "--limit-per-source", "10", "--max-total", "10"])
    assert args.domain == "jobs"
    assert args.jobs_command == "scrape"
    assert args.limit_per_source == 10
    assert args.max_total == 10


def test_cli_embed_mode():
    parser = build_parser()
    args = parser.parse_args(["embed", "build", "--provider", "groq", "--dry-run"])
    assert args.domain == "embed"
    assert args.embed_command == "build"
    assert args.provider == "groq"
    assert args.dry_run is True


def test_cli_degrees_live_aneca_mode():
    parser = build_parser()
    args = parser.parse_args(
        [
            "degrees",
            "catalog",
            "--live-aneca",
            "--cycles",
            "grado,master,doctorado",
            "--limit",
            "5",
            "--with-report-text",
            "--resolve-university-memory",
        ]
    )
    assert args.domain == "degrees"
    assert args.degrees_command == "catalog"
    assert args.live_aneca is True
    assert args.cycles == "grado,master,doctorado"
    assert args.limit == 5
    assert args.with_report_text is True
    assert args.resolve_university_memory is True


def test_cli_jobs_daemon_mode():
    parser = build_parser()
    args = parser.parse_args(
        [
            "jobs",
            "daemon",
            "--window-start",
            "22:00",
            "--window-end",
            "07:30",
            "--timezone",
            "Europe/Madrid",
            "--cooldown-minutes",
            "5",
            "--run-once",
        ]
    )
    assert args.domain == "jobs"
    assert args.jobs_command == "daemon"
    assert args.window_start == "22:00"
    assert args.window_end == "07:30"
    assert args.timezone == "Europe/Madrid"
    assert args.cooldown_minutes == 5
    assert args.run_once is True


def test_cli_degrees_description_alias_sets_same_flag():
    parser = build_parser()
    args = parser.parse_args(["degrees", "catalog", "--with-description-text"])
    assert args.with_report_text is True
