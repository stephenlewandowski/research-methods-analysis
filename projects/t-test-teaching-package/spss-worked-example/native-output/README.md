# Native IBM SPSS output snapshots

These are unmodified text and OMS XML exports from executing the supplied syntax in **IBM SPSS Statistics 29.0.2.0** on 16 October 2026. They are actual native-engine tables. The reconstructed expected tables and `expected_results.json` in the parent directory were calculated independently.

| Analysis | Native text export | Native OMS XML |
| --- | --- | --- |
| Original independent groups | [independent.txt](independent.txt) | [independent.xml](independent.xml) |
| New matched before/after study | [paired.txt](paired.txt) | [paired.xml](paired.xml) |

The independent output corresponds to [ramp_hazard_training.sps](../../ramp_hazard_training.sps). The paired output corresponds to [ramp_hazard_paired.sps](../ramp_hazard_paired.sps), including its descriptive analysis, difference-score diagnostics, paired t-test, and equivalent one-sample test. OMS captures tables here; these snapshot files do not embed the charts. Run the full paired syntax in SPSS to inspect its boxplot, histogram, and normal Q–Q plots.

The text exports wrap long variable labels and round probabilities to the native table's display precision. In the paired test and correlation tables, `.000` means a p-value smaller than the displayed precision, **not a zero probability**. Report the paired test as **p < .001**. The XML contains full-precision numeric attributes used for verification.

The native runner is [source/validate_spss.py](../../source/validate_spss.py), invoked through IBM's `statisticspython3.bat` launcher so the licensed installed engine executes the SPSS syntax. See [BUILD.md](../../BUILD.md) for the reproduction command. The snapshots are provided for students who do not have SPSS available; they do not remove the need to inspect diagnostics and the study design when analyzing new data.

[verified_results.json](verified_results.json) records the full-precision native mean differences, standard errors, t statistics, degrees of freedom, two-sided probabilities, and interval bounds after automated comparison with the independently calculated reference values.
