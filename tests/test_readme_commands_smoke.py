from src.canarias_uni_ml.cli import build_parser


def test_readme_alignment_command_parses():
    parser = build_parser()
    args = parser.parse_args([
        "pipeline",
        "run",
        "--skip-jobs",
        "--skip-degrees",
        "--provider",
        "ollama",
    ])
    assert args.domain == "pipeline"
    assert args.pipeline_command == "run"


def test_readme_jobs_daemon_scale_command_parses():
    parser = build_parser()
    args = parser.parse_args(
        [
            "jobs",
            "daemon",
            "--strategy",
            "scale",
            "--time-limit-minutes",
            "45",
            "--stagnation-cycles",
            "6",
            "--fail-on-stagnation",
        ]
    )
    assert args.domain == "jobs"
    assert args.jobs_command == "daemon"
    assert args.strategy == "scale"


def test_readme_jobs_compact_command_parses():
    parser = build_parser()
    args = parser.parse_args(["jobs", "compact", "--db-path", "data/processed/canarias_jobs.db"])
    assert args.domain == "jobs"
    assert args.jobs_command == "compact"
