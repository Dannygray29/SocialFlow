from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]


def test_required_project_files_exist():
    for relative in ["README.md", ".env.example", ".gitignore", "backend/main.py", "backend/requirements.txt", "frontend/index.html", "vercel.json"]:
        assert (ROOT / relative).is_file(), relative


def test_python_sources_parse():
    for path in sorted((ROOT / "backend").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))

    for path in sorted((ROOT / "api").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))


def test_no_common_secret_placeholders_are_tracked():
    forbidden = ("sk-live-", "sk-proj-", "sk-ant-api", "AIzaSy")
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.name in {"test_integrity.py"}:
            continue
        if path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".json", ".yml", ".yaml", ".md", ".txt", ".env"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert not any(marker in text for marker in forbidden), str(path)


def test_environment_template_does_not_contain_real_credentials():
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "your-heygen-password" not in env
    assert "sk-" not in env
    assert "AIza" not in env
