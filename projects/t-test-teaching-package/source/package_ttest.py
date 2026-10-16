from pathlib import Path
import base64, json, zipfile, csv, shutil, re
from scipy import stats
import numpy as np

out=Path('/workspace/scratch/80d5b05515c0/ttest_animation')
template=(out/'classroom_template.html').read_text()
video=out/'RSCH650_T_Test_Animation.mp4'
poster=out/'qa_scene_2.png'
page=template.replace('__VIDEO_DATA__','data:video/mp4;base64,'+base64.b64encode(video.read_bytes()).decode()).replace('__POSTER_DATA__','data:image/png;base64,'+base64.b64encode(poster.read_bytes()).decode())
assert '__VIDEO_DATA__' not in page and '__POSTER_DATA__' not in page
(out/'RSCH650_T_Test_Classroom.html').write_text(page)

timeline=json.loads((out/'timeline.json').read_text())
def timestamp(sec,sep):
    return f'{int(sec)//3600:02d}:{int(sec)//60%60:02d}:{int(sec)%60:02d}{sep}000'
srt='';vtt='WEBVTT\n\n'
for i,s in enumerate(timeline,1):
    srt+=f'{i}\n{timestamp(s["start"],",")} --> {timestamp(s["end"],",")}\n{s["caption"]}\n\n'
    vtt+=f'{timestamp(s["start"],".")} --> {timestamp(s["end"],".")}\n{s["caption"]}\n\n'
(out/'RSCH650_T_Test_Captions.srt').write_text(srt)
(out/'RSCH650_T_Test_Captions.vtt').write_text(vtt)

# Confirm the supplied rounded CSV reproduces the displayed baseline result.
rows=list(csv.DictReader((out/'ramp_hazard_training.csv').open()))
a=np.array([float(r['report_seconds']) for r in rows if r['training']=='1'])
b=np.array([float(r['report_seconds']) for r in rows if r['training']=='2'])
result=stats.ttest_ind(a,b,equal_var=False)
assert len(a)==len(b)==20
assert abs(result.statistic-2.371708245126282)<1e-8
assert abs(result.pvalue-.022875801799123525)<1e-8
assert abs(a.std(ddof=1)-8)<1e-8 and abs(b.std(ddof=1)-8)<1e-8

# Keep self-contained graphics/code available for future revisions.
source=out/'source';source.mkdir(exist_ok=True)
for name in ['build_ttest_assets.py','render_ttest.py','package_ttest.py']:
    shutil.copyfile(out.parent/name,source/name)
for name in ['assets.json','timeline.json','classroom_template.html']:
    shutil.copyfile(out/name,source/name)

(out/'README.txt').write_text('''RSCH 650 — The t-test on the airport ramp

Start with RSCH650_T_Test_Classroom.html: open it in a desktop browser.
It embeds the video and has chapter buttons, a transcript, and teaching prompts.
The presentation is captioned and has no audio. Duration: 2 minutes 6 seconds.

RSCH650_T_Test_Animation.mp4 can be inserted into a presentation or course page.
Instructor_Notes.md provides the scenario, results, assumptions, and discussion prompts.
ramp_hazard_training.sps contains both SPSS commands and the 40 baseline observations.
ramp_hazard_training.csv provides the same synthetic data for other software.
SRT and VTT files contain the on-screen narration captions for LMS use.

All data are invented for teaching. This is not evidence about actual aviation training.
No internet connection is needed for playback. The method reference links are optional.

The source folder contains the editable template, calculated data, and production scripts.
To rebuild elsewhere, set OUT/out in the Python scripts to your chosen project directory.
The source scripts require Python with NumPy, SciPy, Matplotlib and Pillow, plus FFmpeg.
The delivered HTML and MP4 need none of those dependencies.
''')
files=['README.txt','RSCH650_T_Test_Classroom.html','RSCH650_T_Test_Animation.mp4','Instructor_Notes.md','ramp_hazard_training.csv','ramp_hazard_training.sps','RSCH650_T_Test_Captions.srt','RSCH650_T_Test_Captions.vtt']
bundle=out/'RSCH650_T_Test_Teaching_Package.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name in files:z.write(out/name,name)
    for p in source.iterdir():z.write(p,'source/'+p.name)
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None

# Extract scripts for a syntax-only check in Node.
scripts=re.findall(r'<script>([\s\S]*?)</script>',page)
(out/'qa_player.js').write_text('\n'.join(scripts))
print('Baseline CSV verified against the animation.')
for p in [video,out/'RSCH650_T_Test_Classroom.html',bundle]:
    print(f'{p.name}: {p.stat().st_size:,} bytes')
