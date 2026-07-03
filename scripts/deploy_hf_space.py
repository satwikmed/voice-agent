#!/usr/bin/env python3
"""Create and upload RetellEVA Hugging Face Space for satwikmed."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPACE_ID = os.environ.get("HF_SPACE_ID", "satwikmed/retell-eva")
SPACE_DIR = PROJECT_ROOT / "huggingface-space"


def main() -> None:
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
    if not token:
        print("Set HF_TOKEN (https://huggingface.co/settings/tokens) and re-run.")
        sys.exit(1)

    from huggingface_hub import HfApi

    api = HfApi(token=token)
    api.create_repo(
        repo_id=SPACE_ID,
        repo_type="space",
        space_sdk="streamlit",
        exist_ok=True,
    )

    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        for name in ("app.py", "README.md"):
            shutil.copy(SPACE_DIR / name, dest / name)

        # Space needs project files for imports
        shutil.copytree(
            PROJECT_ROOT / "retell_eva",
            dest / "retell_eva",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        results_src = PROJECT_ROOT / "frontend" / "src" / "data" / "eva-benchmark-results.json"
        data_dir = dest / "frontend" / "src" / "data"
        data_dir.mkdir(parents=True)
        shutil.copy(results_src, data_dir / "eva-benchmark-results.json")

        requirements = """streamlit>=1.35.0
"""
        (dest / "requirements.txt").write_text(requirements, encoding="utf-8")

        # Patch app.py paths for space layout
        app_text = (dest / "app.py").read_text(encoding="utf-8")
        app_text = app_text.replace(
            'PROJECT_ROOT = Path(__file__).resolve().parent.parent',
            'PROJECT_ROOT = Path(__file__).resolve().parent',
        )
        (dest / "app.py").write_text(app_text, encoding="utf-8")

        api.upload_folder(
            folder_path=str(dest),
            repo_id=SPACE_ID,
            repo_type="space",
            commit_message="Deploy RetellEVA demo",
        )

    print(f"Space live: https://huggingface.co/spaces/{SPACE_ID}")


if __name__ == "__main__":
    main()
