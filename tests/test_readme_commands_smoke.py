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
