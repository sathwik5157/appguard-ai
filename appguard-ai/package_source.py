"""Create a source-only ZIP from an explicit allowlist; never package private data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
FILES = ["app.py", "train_model.py", "package_source.py", "README.md", "MODEL_CARD.md",
         "INTERVIEW_GUIDE.md", "SUBMISSION_GUIDE.md", "VERIFICATION.md", "requirements.txt",
         "requirements-lock.txt", "pytest.ini", "launch.cmd", ".gitignore", ".streamlit/config.toml",
         ".github/workflows/tests.yml", "data/README.md", "models/README.md"]


def package():
    paths = [ROOT / p for p in FILES]
    paths += sorted((ROOT / "appguard").glob("*.py"))
    paths += sorted((ROOT / "tests").glob("*.py"))
    paths += sorted((ROOT / "assets").glob("*.png"))
    missing = [str(p.relative_to(ROOT)) for p in paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing package files: {missing}")
    output = ROOT / "dist/appguard-ai-source.zip"
    output.parent.mkdir(exist_ok=True)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, Path("appguard-ai") / path.relative_to(ROOT))
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert not any(name.endswith((".xlsx", ".joblib", ".csv")) for name in archive.namelist())
    print(f"Created {output} ({output.stat().st_size:,} bytes; {len(paths)} files)")


if __name__ == "__main__":
    package()
