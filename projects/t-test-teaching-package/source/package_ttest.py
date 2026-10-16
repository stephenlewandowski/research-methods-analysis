"""Assemble the offline player, captions, editable sources, and teaching ZIP."""

import argparse
import base64
import csv
import json
from pathlib import Path
import shutil
import zipfile

import numpy as np
from scipy import stats


SOURCE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SOURCE_DIR.parent
BUNDLE_NAME = "RSCH650_T_Test_Teaching_Package.zip"
DOCUMENTS = (
    "README.md", "README.txt", "Instructor_Notes.md", "BUILD.md", "requirements.txt", "REVIEW.md",
)
DELIVERABLES = (
    "RSCH650_T_Test_Classroom.html", "RSCH650_T_Test_Animation.mp4",
    "ramp_hazard_training.csv", "ramp_hazard_training.sps",
    "RSCH650_T_Test_Captions.srt", "RSCH650_T_Test_Captions.vtt",
)


def copy_if_different(source, destination):
    """Copy a source input while allowing an in-place build."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def copy_tree(source, destination):
    if not source.exists():
        return []
    paths = []
    for original in sorted(source.rglob("*")):
        if original.is_file() and "__pycache__" not in original.parts:
            relative = original.relative_to(source)
            copy_if_different(original, destination / relative)
            paths.append(destination / relative)
    return paths


def timestamp(seconds, separator):
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}{separator}{milliseconds:03d}"


def verify_baseline(csv_path):
    # Confirm the rounded, exported CSV reproduces the displayed result.
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    a = np.array([float(row["report_seconds"]) for row in rows if row["training"] == "1"])
    b = np.array([float(row["report_seconds"]) for row in rows if row["training"] == "2"])
    result = stats.ttest_ind(a, b, equal_var=False)
    assert len(a) == len(b) == 20
    assert abs(result.statistic - 2.371708245126282) < 1e-8
    assert abs(result.pvalue - .022875801799123525) < 1e-8
    assert abs(a.std(ddof=1) - 8) < 1e-8 and abs(b.std(ddof=1) - 8) < 1e-8


def package(output_dir):
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    video = out / "RSCH650_T_Test_Animation.mp4"
    poster = out / "poster.png"
    for needed in [video, poster, out / "source" / "assets.json", out / "source" / "timeline.json",
                   out / "ramp_hazard_training.csv", out / "ramp_hazard_training.sps"]:
        if not needed.is_file():
            raise FileNotFoundError(f"Missing build output: {needed}. Run source/build.py first.")

    template = (SOURCE_DIR / "classroom_template.html").read_text(encoding="utf-8")
    page = template.replace(
        "__VIDEO_DATA__", "data:video/mp4;base64," + base64.b64encode(video.read_bytes()).decode("ascii")
    ).replace(
        "__POSTER_DATA__", "data:image/png;base64," + base64.b64encode(poster.read_bytes()).decode("ascii")
    )
    assert "__VIDEO_DATA__" not in page and "__POSTER_DATA__" not in page
    (out / "RSCH650_T_Test_Classroom.html").write_text(page, encoding="utf-8", newline="\n")

    timeline = json.loads((out / "source" / "timeline.json").read_text(encoding="utf-8"))
    srt, vtt = [], ["WEBVTT\n\n"]
    for index, scene in enumerate(timeline, 1):
        srt.append(f'{index}\n{timestamp(scene["start"], ",")} --> '
                   f'{timestamp(scene["end"], ",")}\n{scene["caption"]}\n\n')
        vtt.append(f'{timestamp(scene["start"], ".")} --> '
                   f'{timestamp(scene["end"], ".")}\n{scene["caption"]}\n\n')
    (out / "RSCH650_T_Test_Captions.srt").write_text("".join(srt), encoding="utf-8", newline="\n")
    (out / "RSCH650_T_Test_Captions.vtt").write_text("".join(vtt), encoding="utf-8", newline="\n")
    verify_baseline(out / "ramp_hazard_training.csv")

    # Source inputs are always read beside this script, never from the working directory.
    source_out = out / "source"
    for original in sorted(SOURCE_DIR.glob("*.py")):
        copy_if_different(original, source_out / original.name)
    copy_if_different(SOURCE_DIR / "classroom_template.html", source_out / "classroom_template.html")
    for name in DOCUMENTS:
        copy_if_different(PACKAGE_DIR / name, out / name)
    tree_files = []
    for folder in ["spss-worked-example", "review", "tests"]:
        tree_files.extend(copy_tree(PACKAGE_DIR / folder, out / folder))

    files = [out / name for name in (*DOCUMENTS, *DELIVERABLES)]
    files.extend(sorted(path for path in source_out.iterdir() if path.is_file()
                        and path.suffix in {".py", ".json", ".html"}))
    files.extend(tree_files)
    bundle = out / BUNDLE_NAME
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(out).as_posix())
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
    print("Baseline CSV verified against the animation.")
    for path in [video, out / "RSCH650_T_Test_Classroom.html", bundle]:
        print(f"{path}: {path.stat().st_size:,} bytes")
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PACKAGE_DIR,
                        help="Directory holding rendered outputs (default: package directory).")
    args = parser.parse_args()
    package(args.output_dir)


if __name__ == "__main__":
    main()
