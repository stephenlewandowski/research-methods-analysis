from pathlib import Path
import json, csv
import numpy as np
from scipy import stats

OUT = Path('/workspace/scratch/80d5b05515c0/ttest_animation')
OUT.mkdir(exist_ok=True)

def sample(n, mean, sd, seed):
    # Engineered synthetic samples: exact teaching means/SD, no real workers.
    rng = np.random.default_rng(seed)
    z = rng.normal(size=n)
    z = (z-z.mean())/z.std(ddof=1)
    return mean+sd*z

scenarios = {}
for key,n,gap,sd in [('baseline',20,6,8),('gap',20,12,8),('scatter',20,6,14),('size',80,6,14)]:
    a = sample(n,48,sd,246)
    b = sample(n,48-gap,sd,739)
    assert min(a.min(),b.min()) > 0
    v1,v2 = a.var(ddof=1)/n,b.var(ddof=1)/n
    se = np.sqrt(v1+v2)
    df = (v1+v2)**2/(v1*v1/(n-1)+v2*v2/(n-1))
    t = (a.mean()-b.mean())/se
    p = 2*stats.t.sf(abs(t),df)
    ci = (gap-stats.t.ppf(.975,df)*se,gap+stats.t.ppf(.975,df)*se)
    check=stats.ttest_ind(a,b,equal_var=False)
    assert abs(t-check.statistic)<1e-12 and abs(p-check.pvalue)<1e-12
    scenarios[key] = dict(n=n,gap=gap,sd=sd,meanA=48,meanB=48-gap,se=float(se),df=float(df),t=float(t),p=float(p),ci=list(ci),a=a.tolist(),b=b.tolist())

# Fixed shared axis across all teaching examples.
all_values=[v for d in scenarios.values() for k in ['a','b'] for v in d[k]]
lo=10*np.floor(min(all_values)/10)
hi=10*np.ceil(max(all_values)/10)
tx=np.linspace(-5.5,5.5,551)
curve=[(float(x),float(stats.t.pdf(x,38))) for x in tx]
assets=dict(scenarios=scenarios,domain=[float(lo),float(hi)],curve=curve)
(OUT/'assets.json').write_text(json.dumps(assets,separators=(',',':')))

with (OUT/'ramp_hazard_training.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['worker_id','training','report_seconds'])
    for group,k in [(1,'a'),(2,'b')]:
        for i,x in enumerate(scenarios['baseline'][k],1):
            w.writerow([f'{group}{i:02d}',group,f'{x:.9f}'])

sps='''* RSCH 650: synthetic ramp hazard reporting example.
* Each row is one different worker; all observations are invented for teaching.
* Group 1 = standard briefing; group 2 = scenario practice.
* Outcome = seconds to correctly report a hazard in a standardized simulator task.
* Read the Equal variances not assumed row for the Welch test.
DATA LIST FREE /worker_id (F3.0) training (F1.0) report_seconds (F12.9).
BEGIN DATA
'''
for group,k in [(1,'a'),(2,'b')]:
    for i,x in enumerate(scenarios['baseline'][k],1):
        sps+=f'{group}{i:02d} {group} {x:.9f}\n'
sps+='''END DATA.
DATASET NAME RampHazard.
VARIABLE LABELS training 'Assigned training method'
 report_seconds 'Time to correctly report a simulated ramp hazard (seconds)'.
VALUE LABELS training 1 'Standard briefing' 2 'Scenario practice'.
VARIABLE LEVEL training (NOMINAL) report_seconds (SCALE).
FORMATS report_seconds (F8.2).
T-TEST GROUPS=training(1 2)
 /VARIABLES=report_seconds
 /MISSING=ANALYSIS
 /CRITERIA=CI(.95).
'''
(OUT/'ramp_hazard_training.sps').write_text(sps)
print(json.dumps({k:{x:v[x] for x in ['n','gap','sd','se','df','t','p','ci']} for k,v in scenarios.items()},indent=2))
