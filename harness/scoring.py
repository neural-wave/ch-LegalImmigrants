"""The official scoring module, loaded from the repository root (`scoring.py`) so the harness never diverges from it."""
import importlib.util
import sys

from harness import paths

_spec = importlib.util.spec_from_file_location("harness.scoring", paths.REPO / "scoring.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
sys.modules[__name__] = _module
