"""Rebuild shareable figures from the included aggregate data, without raw exports."""
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
for script in ['build_figures.py','build_journey.py','build_paper.py']:
    subprocess.run([sys.executable,str(HERE/script)],check=True)
