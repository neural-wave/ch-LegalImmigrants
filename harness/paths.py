"""Default folders of the challenge, relative to this repository (override them with the CLI flags)."""
import pathlib

HARNESS = pathlib.Path(__file__).resolve().parent
REPO = HARNESS.parent
LIFEWARE = REPO.parent
DATA = LIFEWARE / "data"
LEGACY = DATA / "legacy"
TARGETS = DATA / "targets"
STARTER_KIT = DATA / "starter_kit"
SUBMISSION = REPO / "my_solution"
REPORTS = HARNESS / "reports"
