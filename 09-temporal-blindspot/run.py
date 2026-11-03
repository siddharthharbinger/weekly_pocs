"""Run this POC from any working directory."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from poc_lab.cli import main

if __name__ == "__main__":
    main("09")
