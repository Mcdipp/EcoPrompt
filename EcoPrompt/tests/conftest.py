"""Configuration pytest : rend les modules du projet importables depuis tests/."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
