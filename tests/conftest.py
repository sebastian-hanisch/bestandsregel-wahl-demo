"""Gemeinsame Einstellungen: Wurzelordner im Importpfad, ein BLAS-Thread (kleine Matrizen: mehrere Threads bremsen unter Last um ein Vielfaches)."""

import os
import sys
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
