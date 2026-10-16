# Two-sided Welch t-test simulation

An interactive teaching example for RSCH650 showing how the difference between two sample means, relative to its standard error, produces a t-statistic and a two-sided p-value.

## Run

Download or clone the repository, then open [index.html](index.html) in a modern browser. GitHub's file view displays the source rather than running the simulation. No installation or server is required. An internet connection is needed to load D3 7.9.0 from jsDelivr.

## Explore

- Adjust the true mean difference (B minus A), sample size per group, and shared population standard deviation.
- Select **Draw new samples** to see observations, sample means, the mean difference, standard error, t-statistic, p-value, and 95% confidence interval.
- The reference t distribution shades both tails beyond the observed absolute t-statistic. Their total probability is the two-sided p-value; dashed lines mark the rejection cutoffs at alpha = 0.05.
- Set the true difference to **0** and select **Run 200 experiments** to explore false positives. With a nonzero true difference, the rejection percentage estimates power. Percentages vary between batches.

The p-value describes results at least as extreme under the null hypothesis of equal population means; it is not the probability that the null hypothesis is true. A result that does not reject the null does not establish that the means are equal.

## Model and reproducibility

All observations are synthetic, generated in the browser from independent normal populations. Group A's population mean is 0, group B's mean is the selected difference, and both populations use the selected standard deviation. There are no input datasets or server requests for data.

The analysis uses separate sample variances, the Welch-Satterthwaite degrees of freedom, and a two-sided test at alpha = 0.05. The 95% interval uses the same degrees of freedom. The test supports unequal variances, although this demonstration uses a shared population standard deviation.

The initial seed is **23**, with 30 observations per group, a true difference of 0.6, and population SD of 1.0. Sampling uses a seeded pseudorandom generator and a Box-Muller normal transform. Sliders retain the seed so parameter changes can be compared; the two action buttons choose new seeds. The standalone export keeps the latest settings and seeds in browser local storage where available. Clearing this page's saved browser state restores the initial values.

## Files

- [simulation.html](simulation.html): original editable visualization fragment, including the sampling, statistical calculations, and chart code.
- [index.html](index.html): standalone export, including the layout, theme styles, and browser state support needed outside the chat.

To regenerate the standalone export after editing the fragment, use the renderer bundled with the Codex visualize skill:

```sh
python /path/to/visualize/scripts/render.py simulation.html index.html --title "RSCH650 | Two-sided Welch t-test simulation" --force
```

The renderer is required only to rebuild the export, not to run it.

## Reference

[NIST/SEMATECH Engineering Statistics Handbook: Two-Sample t-Test for Equal Means](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm), including the Welch-Satterthwaite degrees of freedom.
