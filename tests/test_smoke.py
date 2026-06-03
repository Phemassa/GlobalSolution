from pathlib import Path


def test_project_scaffold_exists() -> None:
    required = [
        Path("docs"),
        Path("src"),
        Path("data"),
        Path("PROJECT_PLAN.md"),
    ]
    for item in required:
        assert item.exists(), f"Missing required path: {item}"
