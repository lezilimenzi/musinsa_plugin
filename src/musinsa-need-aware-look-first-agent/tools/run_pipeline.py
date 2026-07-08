from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an emergent-theme, keyword-led full-body Look-first slot plan (live only).")
    parser.add_argument("--as-of", help="Analysis date in YYYY-MM-DD")
    parser.add_argument("--clean-output", action="store_true")
    args = parser.parse_args()
    result = run(as_of=args.as_of, clean_output=args.clean_output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
