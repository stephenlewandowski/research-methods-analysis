# The t-test on the airport ramp

A teaching package for RSCH650, created in ChatGPT Work and supplied as `RSCH650_T_Test_Teaching_Package.zip`. It compares standard briefing with scenario practice using synthetic times to correctly report a simulated ramp hazard.

The package contains a **2 minute, 6 second captioned animation without audio**, an offline classroom player, instructor prompts, synthetic data, SPSS syntax, captions, and production sources.

## Start here

Download or clone the repository and open [RSCH650_T_Test_Classroom.html](RSCH650_T_Test_Classroom.html) in a desktop browser. The player embeds the video and poster, has nine chapter buttons, and includes a text transcript and results table. It works offline. GitHub's HTML file view displays the source rather than running the player.

The two issues in the initial [quality review](REVIEW.md) have been corrected. Chapter 7 shows the complete 80-per-group observations and matching statistics from **1:23**, and the [portable build](BUILD.md) works from the supplied source layout. The independent and paired syntax files have both been executed successfully in **IBM SPSS Statistics 29.0.2.0** and checked against independent calculations.

For a guided software exercise, start with the [SPSS worked examples](spss-worked-example/): a walkthrough of the original independent-group analysis and a separate paired before/after study, with data, syntax, expected results, native SPSS output, and exercises.

## Included materials

| Material | Purpose |
| --- | --- |
| [Classroom player](RSCH650_T_Test_Classroom.html) | Offline video, chapters, transcript, results, and instructor prompts |
| [Animation](RSCH650_T_Test_Animation.mp4) | H.264 video, 1280 × 720, 15 fps, no audio track |
| [Instructor notes](Instructor_Notes.md) | Scenario, objectives, assumptions, expected results, and discussion stops |
| [Dataset](ramp_hazard_training.csv) | 40 synthetic observations, 20 workers per independent group |
| [SPSS syntax](ramp_hazard_training.sps) | Embedded baseline observations and independent-samples t-test commands |
| [SPSS worked examples](spss-worked-example/) | Guided independent and paired analyses, a separate matched dataset, exercises, and native output |
| [SRT captions](RSCH650_T_Test_Captions.srt) / [WebVTT captions](RSCH650_T_Test_Captions.vtt) | Nine timed text segments for compatible course platforms |
| [Production sources](source/) | Python generation/rendering/packaging scripts, calculated assets, timeline, and HTML template |
| [Build instructions](BUILD.md) | Dependency installation, one-command rebuild, and verification |
| [Quick-start README](README.txt) | Playback and build entry points |

## Dataset

All data are invented for instruction and engineered to exact teaching means and sample SDs. They are not observations about real personnel or evidence of aviation-training effectiveness.

| Variable | Meaning |
| --- | --- |
| `worker_id` | Synthetic worker identifier; one row per worker |
| `training` | 1 = standard briefing; 2 = scenario practice |
| `report_seconds` | Seconds until a correct report in the hypothetical simulator task; lower is faster |

The original numerical outcome uses briefing minus practice, so a positive difference favors practice on this measure. The video identifies the paired design conceptually; the new [worked example](spss-worked-example/) develops it with a separate before/after dataset. The original independent workers are never reinterpreted as pairs.

## Rebuild

Install the pinned [requirements](requirements.txt) and FFmpeg, then run `python source/build.py` from this directory. The default rebuild updates the delivered files in place; `--output-dir "build/classroom copy"` produces a separate package. See [BUILD.md](BUILD.md) for complete setup, individual stages, regression checks, and native SPSS validation.

## Provenance

The original 14-file ZIP was imported byte-for-byte in [commit 8859fe6](https://github.com/stephenlewandowski/research-methods-analysis/commit/8859fe6d792650d1f9c4d1c67dc6ee9b716e8603). This revised edition fixes the renderer and production scripts, rebuilds the delivered video/player, and adds the SPSS lab and validation material. The initial review and its two screenshots remain as an audit record; they show the original video rather than the corrected edition.

Original source archive SHA-256 (not a checksum of the revised package):

```text
e2f4ac100e0315a651b657846d9d73b640b27c62e2f27a8ff4fb19870d5dff0f
```

Related interactive example: [Two-sided Welch t-test simulation](../../code/welch-t-test/).
