"""Entry point for `python -m arena`."""
import sys
from pathlib import Path

# Make `python -m arena` work even if the repo root is not the current directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arena.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
