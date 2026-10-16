# The t-test on the airport ramp

A teaching package for RSCH650, created in ChatGPT Work and supplied as `RSCH650_T_Test_Teaching_Package.zip`. It compares standard briefing with scenario practice using synthetic times to correctly report a simulated ramp hazard.

The package contains a **2 minute, 6 second captioned animation without audio**, an offline classroom player, instructor prompts, synthetic data, SPSS syntax, captions, and production sources.

## Start here

Download or clone the repository and open [RSCH650_T_Test_Classroom.html](RSCH650_T_Test_Classroom.html) in a desktop browser. The player embeds the video and poster, has nine chapter buttons, and includes a text transcript and results table. It works offline. GitHub's HTML file view displays the source rather than running the player.

Read the independent [quality review](REVIEW.md) before teaching from the package. The completed-scene statistics check out. A transition at chapter 7 briefly pairs the old points with the new sample-size statistics: advance to **1:26** for the settled larger-sample display. Rebuilding the supplied source requires more setup than the original README describes. The SPSS syntax has not been executed in SPSS.

## Included materials

| Material | Purpose |
| --- | --- |
| [Classroom player](RSCH650_T_Test_Classroom.html) | Offline video, chapters, transcript, results, and instructor prompts |
| [Animation](RSCH650_T_Test_Animation.mp4) | H.264 video, 1280 × 720, 15 fps, no audio track |
| [Instructor notes](Instructor_Notes.md) | Scenario, objectives, assumptions, expected results, and discussion stops |
| [Dataset](ramp_hazard_training.csv) | 40 synthetic observations, 20 workers per independent group |
| [SPSS syntax](ramp_hazard_training.sps) | Embedded baseline observations and independent-samples t-test commands |
| [SRT captions](RSCH650_T_Test_Captions.srt) / [WebVTT captions](RSCH650_T_Test_Captions.vtt) | Nine timed text segments for compatible course platforms |
| [Production sources](source/) | Python generation/rendering/packaging scripts, calculated assets, timeline, and HTML template |
| [Original README](README.txt) | Supplied package instructions |

## Dataset

All data are invented for instruction and engineered to exact teaching means and sample SDs. They are not observations about real personnel or evidence of aviation-training effectiveness.

| Variable | Meaning |
| --- | --- |
| `worker_id` | Synthetic worker identifier; one row per worker |
| `training` | 1 = standard briefing; 2 = scenario practice |
| `report_seconds` | Seconds until a correct report in the hypothetical simulator task; lower is faster |

The numerical outcome uses briefing minus practice, so a positive difference favors practice on this measure. The paired design is discussed conceptually; the supplied data and SPSS analysis are for independent groups.

## Provenance

All 14 files from the supplied ZIP were extracted with their original paths and contents. Repository integration adds this README, [REVIEW.md](REVIEW.md), `.gitattributes`, and the two review screenshots; it does not repair the supplied product. Each extracted file was checked byte-for-byte against its archive entry, and `.gitattributes` preserves the original line endings in Git.

Source archive SHA-256:

```text
e2f4ac100e0315a651b657846d9d73b640b27c62e2f27a8ff4fb19870d5dff0f
```

Related interactive example: [Two-sided Welch t-test simulation](../../code/welch-t-test/).
