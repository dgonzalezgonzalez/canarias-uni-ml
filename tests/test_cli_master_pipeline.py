from src.canarias_uni_ml.cli import build_parser


def test_cli_align_mode():
    parser = build_parser()
    args = parser.parse_args(["align", "run", "--provider", "ollama", "--min-text-len", "20"])
    assert args.domain == "align"
    assert args.align_command == "run"
    assert args.provider == "ollama"
    assert args.min_text_len == 20


def test_cli_pipeline_mode():
    parser = build_parser()
    args = parser.parse_args(["pipeline", "run", "--skip-jobs", "--provider", "openai"])
    assert args.domain == "pipeline"
    assert args.pipeline_command == "run"
    assert args.skip_jobs is True
    assert args.provider == "openai"
