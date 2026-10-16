"""Default folders of the challenge, relative to this repository (override them with the CLI flags).

The partner's data is not in the repository: put it in `data/` next to this file's parent (git-ignored) or one
level above the repository, or pass `--legacy` / `--targets`.
"""
import pathlib

HARNESS = pathlib.Path(__file__).resolve().parent
REPO = HARNESS.parent
LIFEWARE = REPO.parent
DATA = REPO / "data" if (REPO / "data").exists() else LIFEWARE / "data"
LEGACY = DATA / "legacy"
TARGETS = DATA / "targets"
SUBMISSION = REPO / "my_solution"
REPORTS = HARNESS / "reports"
