"""Rebuild the complete RSCH650 t-test teaching package from a checkout or ZIP."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


SOURCE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SOURCE_DIR.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR,
                        help="Destination directory (default: package directory).")
    parser.add_argument("--ffmpeg", help="Path to the FFmpeg executable; otherwise use PATH.")
    args = parser.parse_args()
    ffmpeg = shutil.which(args.ffmpeg or "ffmpeg")
    if ffmpeg is None:
        parser.error("FFmpeg was not found. Install FFmpeg, add it to PATH, or pass --ffmpeg PATH.")
    out = args.output_dir.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    common = ["--output-dir", str(out)]
    stages = [
        ("Generate synthetic data and statistical assets", "build_ttest_assets.py", common),
        ("Render chapter previews and the classroom poster", "render_ttest.py", common),
        ("Encode the 2:06 captioned animation", "render_ttest.py", common + ["--encode", "--ffmpeg", ffmpeg]),
        ("Assemble the player, captions, teaching materials, and ZIP", "package_ttest.py", common),
    ]
    for index, (description, name, options) in enumerate(stages, 1):
        print(f"[{index}/{len(stages)}] {description}", flush=True)
        subprocess.run([sys.executable, str(SOURCE_DIR / name), *options], check=True)
    print(f"Build complete: {out / 'RSCH650_T_Test_Teaching_Package.zip'}", flush=True)


if __name__ == "__main__":
    main()
