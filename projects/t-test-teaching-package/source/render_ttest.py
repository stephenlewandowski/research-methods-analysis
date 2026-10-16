from pathlib import Path
import argparse, json, math, textwrap, subprocess, shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import t as tdist
from PIL import Image
from matplotlib.font_manager import FontProperties

SOURCE_DIR=Path(__file__).resolve().parent
OUT=SOURCE_DIR.parent
ASSETS={}
S={}
BG='#F6F8FA'; INK='#182F43'; MUTED='#526878'; GRID='#D5DEE5'
BLUE='#216A9A'; AMBER='#AE570D'; BLUE_LIGHT='#D9EAF5'; ACCENT='#247C72'
W,H,FPS=1280,720,15

SCENES=[
dict(start=0,end=14,key='baseline',title='Does practice improve hazard reporting?',subtitle='A hypothetical study with airport ground personnel',
caption='Randomly assign 40 workers to two training methods. Each worker completes one identical simulator task: correctly report a ramp hazard.',note='One dot = one worker'),
dict(start=14,end=27,key='baseline',title='Start with the difference in averages',subtitle='Outcome: seconds to correctly report the hazard · Lower is faster',
caption='The practice group averages 42 seconds; the briefing group averages 48. The observed difference is 6 seconds, but individual results overlap.',note='Difference = briefing − practice'),
dict(start=27,end=42,key='baseline',title='Compare the gap with its uncertainty',subtitle='The t statistic expresses the mean difference in standard-error units',
caption='The standard error of the difference is 2.53 seconds. A 6-second gap is 2.37 standard errors from zero. Individual SD and standard error are different.',note='SD = variation among workers'),
dict(start=42,end=59,key='baseline',title='How unusual is a t value of 2.37?',subtitle='Reference distribution if the population means are equal · Two-sided test',
caption='If equal population means and the model assumptions hold, about 2.3% of t values are this far from zero or farther, in either direction.',note='p is not the probability that H₀ is true'),
dict(start=59,end=70,key='gap',title='A larger gap strengthens the evidence',subtitle='Separate illustration · Same sample size and individual variability',
caption='Double the mean difference from 6 to 12 seconds, keeping the same sample size and spread. The t value doubles, and the p-value becomes smaller.',note='Only the mean difference changes'),
dict(start=70,end=83,key='scatter',title='More variability weakens the evidence',subtitle='Separate illustration · Return to a 6-second gap and 20 workers per group',
caption='Now increase the individual SD from 8 to 14 seconds. The same 6-second gap is less precise: p = .183. This does not establish that the methods are equal.',note='Same gap; more scatter among workers'),
dict(start=83,end=96,key='size',title='A larger planned sample improves precision',subtitle='Separate illustration · Same 6-second gap and 14-second individual SD',
caption='Compare a planned study of 80 workers per group with 20. The individual spread stays the same, but the standard error of the difference is halved.',note='Separate study sizes; not a stopping rule'),
dict(start=96,end=112,key='baseline',title='Report the effect and its uncertainty',subtitle='Return to the original 20-per-group example',
caption='The estimated advantage is 6 seconds, with a 95% confidence interval from 0.9 to 11.1 seconds. Decide whether that range matters operationally.',note='Briefing − practice · Positive favors practice'),
dict(start=112,end=126,key='baseline',title='Match the test to the study design',subtitle='Independent groups here · A paired test answers a different design',
caption='Different workers in each group: use a two-sample t-test. The same workers before and after training: consider a paired t-test. Check assumptions first.',note='Simulator performance is not an incident rate'),
]

def configure(output_dir):
    global OUT,ASSETS,S
    OUT=Path(output_dir).expanduser().resolve()
    OUT.mkdir(parents=True,exist_ok=True)
    assets_path=OUT/'source'/'assets.json'
    if not assets_path.is_file():assets_path=OUT/'assets.json'
    if not assets_path.is_file():
        raise FileNotFoundError(f'Missing {assets_path}; run build_ttest_assets.py --output-dir "{OUT}" first.')
    ASSETS=json.loads(assets_path.read_text(encoding='utf-8'))
    S=ASSETS['scenarios']

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':GRID,'savefig.facecolor':BG})
fig=plt.figure(figsize=(W/100,H/100),dpi=100,facecolor=BG)

def smooth(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def pstr(p):return '< .001' if p<.001 else '= '+f'{p:.3f}'.lstrip('0')
def text(x,y,s,size=16,color=INK,weight='normal',ha='left',va='top',**kw):
    return fig.text(x,y,s,fontsize=size,color=color,weight=weight,ha=ha,va=va,**kw)
def wrap(s,n=100):return '\n'.join(textwrap.wrap(s,n,break_long_words=False))
def caption_wrap(s):
    renderer=fig.canvas.get_renderer();font=FontProperties(family='DejaVu Sans',size=17)
    lines=[];line=''
    for word in s.split():
        candidate=(line+' '+word).strip()
        width=renderer.get_text_width_height_descent(candidate,font,False)[0]
        if width>W*.90 and line:lines.append(line);line=word
        else:line=candidate
    if line:lines.append(line)
    assert len(lines)<=2,lines
    return '\n'.join(lines)
def axes(rect,xlabel,ylabel=None):
    ax=fig.add_axes(rect,facecolor=BG)
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['bottom','left']].set_color(GRID)
    ax.tick_params(length=0,pad=8,labelsize=13)
    ax.set_xlabel(xlabel,labelpad=12,fontsize=14)
    if ylabel:ax.set_ylabel(ylabel,labelpad=10,fontsize=14)
    return ax

def swarm(vals,group):
    # Place each observation without changing its horizontal data value.
    order=np.argsort(vals);used=[];ys=np.empty(len(vals))
    for i in order:
        x=vals[i]
        candidates=[0]+[j*.105*s for j in range(1,10) for s in [1,-1]]
        for off in candidates:
            if all(((x-u)/1.35)**2+((off-v)/.115)**2>=1 for u,v in used):break
        ys[i]=group+off;used.append((x,off))
    return ys

def data_at(idx,u):
    key=SCENES[idx]['key']; target=S[key]
    if idx==4:source=S['baseline']
    elif idx==5:source=S['baseline']
    else:return target
    d=dict(target)
    for k in ['a','b']:d[k]=(np.array(source[k])*(1-u)+np.array(target[k])*u).tolist()
    for k in ['meanA','meanB','gap','sd','se','t']:d[k]=source[k]*(1-u)+target[k]*u
    # Compute statistics from the actual interpolated observations.
    a=np.array(d['a']);b=np.array(d['b']);n=len(a)
    v1=a.var(ddof=1)/n;v2=b.var(ddof=1)/n
    d['se']=float(np.sqrt(v1+v2));d['t']=float((a.mean()-b.mean())/d['se'])
    d['df']=float((v1+v2)**2/(v1*v1/(n-1)+v2*v2/(n-1)))
    d['p']=float(2*tdist.sf(abs(d['t']),d['df']))
    return d

def metric(y,label,value,detail=''):
    text(.755,y,label,13,MUTED)
    text(.755,y-.038,value,31)
    if detail:text(.755,y-.098,detail,13,MUTED)

def dot_plot(idx,u,d):
    ax=axes([.095,.285,.60,.405],'Time to correctly report the hazard (seconds)')
    ax.set_xlim(*ASSETS['domain']);ax.set_ylim(-.75,2.3)
    ax.set_yticks([1.3,0],['Briefing','Practice']);ax.tick_params(axis='y',labelsize=15)
    ax.set_xticks(np.arange(ASSETS['domain'][0],ASSETS['domain'][1]+1,10))
    ax.grid(axis='x',color=GRID,alpha=.55,linewidth=.6);ax.set_axisbelow(True)
    ax.spines['left'].set_visible(False)
    n=d['n']
    for k,mean,col,y,marker in [('a',d['meanA'],BLUE,1.3,'o'),('b',d['meanB'],AMBER,0,'s')]:
        vals=np.array(d[k]);ys=swarm(vals,y)
        # A new planned study starts with its complete observations and matching
        # statistics, including when the chapter button pauses on its first frame.
        ax.scatter(vals,ys,s=47 if n==20 else 31,marker=marker,color=col,zorder=3)
        if idx>=1:
            length=.35*(u if idx==1 else 1)
            ax.plot([mean,mean],[y-length,y+length],color=col,linewidth=3.4,zorder=4)
            ax.text(mean,y+.55,f'Mean {mean:.0f} s',ha='center',va='bottom',color=INK,fontsize=14)
        if idx>=2:
            span=d['sd']*(u if idx==2 else 1)
            ax.plot([mean-span,mean+span],[y-.52,y-.52],color=col,linewidth=2)
            ax.plot([mean-span,mean-span],[y-.56,y-.48],color=col,linewidth=2)
            ax.plot([mean+span,mean+span],[y-.56,y-.48],color=col,linewidth=2)
    if idx>=1:
        a,b=d['meanA'],d['meanB']
        ax.annotate('',xy=(a,2.16),xytext=(b,2.16),arrowprops=dict(arrowstyle='<->',color=INK,lw=1.6))
    text(.10,.735,'STANDARD BRIEFING   ●',13,BLUE)
    text(.40,.735,'SCENARIO PRACTICE   ■',13,AMBER)
    bottom=f"n = {n} in each group"
    if idx>=2:bottom+=f"   ·   Bars show mean ± 1 individual SD ({d['sd']:.0f} s)"
    text(.10,.195,bottom,13,MUTED)

def null_plot(u):
    ax=axes([.095,.285,.60,.405],'t statistic (standard-error units)','Density')
    xx=np.linspace(-5.5,5.5,1201);yy=tdist.pdf(xx,38);tv=S['baseline']['t']
    ax.set_xlim(-5.5,5.5);ax.set_ylim(0,.45)
    ax.set_xticks([-4,-2,0,2,4]);ax.set_yticks([0,.2,.4])
    ax.grid(axis='y',color=GRID,alpha=.5,linewidth=.6)
    ax.plot(xx,yy,color=BLUE,linewidth=3)
    for sign in [-1,1]:
        xx2=np.linspace(-5.5,-tv,400) if sign<0 else np.linspace(tv,5.5,400)
        ax.fill_between(xx2,tdist.pdf(xx2,38),color=AMBER,alpha=.35+.4*u)
        ax.vlines(sign*tv,0,tdist.pdf(tv,38)+.045,color=AMBER,linewidth=2)
        ax.text(sign*tv,tdist.pdf(tv,38)+.065,f'{sign*tv:+.2f}',ha='center',fontsize=14,color=INK)
    ax.axvline(0,color=GRID,lw=1)
    ax.text(0,.427,'No population mean difference',ha='center',fontsize=14,color=INK)
    text(.10,.735,'REFERENCE t DISTRIBUTION   ·   df = 38',13,MUTED)
    text(.10,.195,'Shaded tails: outcomes at least as extreme as the observed t',13,MUTED)

def ci_plot(u):
    d=S['baseline'];lo,hi=d['ci']
    ax=axes([.095,.315,.60,.34],'Mean difference: briefing − practice (seconds)')
    ax.set_xlim(-3,15);ax.set_ylim(-.8,.9);ax.set_yticks([])
    ax.spines['left'].set_visible(False);ax.set_xticks([-2,0,3,6,9,12,15])
    ax.grid(axis='x',color=GRID,alpha=.5,linewidth=.6)
    ax.axvline(0,color=MUTED,lw=1.5,ls='--')
    ax.text(0,.70,'No difference',ha='center',fontsize=14)
    # Expand from the point estimate to the final interval.
    left=6+(lo-6)*u;right=6+(hi-6)*u
    ax.hlines(0,left,right,color=BLUE,lw=5)
    ax.vlines([left,right],-.12,.12,color=BLUE,lw=2)
    ax.scatter([6],[0],s=160,color=BLUE,zorder=4)
    ax.text(6,.30,'6.0 s',ha='center',fontsize=21)
    if u>.98:
        ax.text(lo,-.30,f'{lo:.1f}',ha='center',fontsize=16)
        ax.text(hi,-.30,f'{hi:.1f}',ha='center',fontsize=16)
    ax.text(-2.6,-.68,'Briefing faster',fontsize=13,ha='left',color=MUTED)
    ax.text(14.6,-.68,'Practice faster',fontsize=13,ha='right',color=MUTED)
    text(.10,.735,'95% CONFIDENCE INTERVAL FOR THE MEAN DIFFERENCE',13,MUTED)
    text(.10,.195,'Magnitude + uncertainty + operational context',14,MUTED)

def design_plot(u):
    ax=fig.add_axes([.085,.28,.62,.44],facecolor=BG)
    ax.set_xlim(0,10);ax.set_ylim(-.2,4.3);ax.axis('off')
    ax.text(0,4.0,'Different workers',fontsize=19,weight='medium')
    for i in range(7):
        ax.scatter(.35+i*.48,3.25,s=95,color=BLUE,marker='o')
        ax.scatter(.35+i*.48,2.72,s=95,color=AMBER,marker='s')
    ax.text(4.3,3.12,'Welch two-sample t-test',fontsize=19)
    ax.text(0,1.85,'Same workers measured twice',fontsize=19,weight='medium')
    for i in range(7):
        x=.35+i*.48
        ax.plot([x,x],[.58,1.10],color=GRID,lw=1.5)
        ax.scatter(x,1.10,s=95,color=BLUE,marker='o')
        ax.scatter(x,.58,s=95,color=AMBER,marker='s')
    ax.text(4.3,.95,'Paired t-test',fontsize=19)
    text(.10,.195,'Linked measurements require a design that accounts for the pairing.',13,MUTED)

def draw(idx,elapsed):
    fig.clear();fig.set_facecolor(BG);sc=SCENES[idx]
    u=smooth(elapsed/2.4)
    text(.05,.956,'RSCH 650   /   RESEARCH METHODS & ANALYSIS',12,MUTED)
    text(.95,.956,'AVIATION SAFETY',12,MUTED,ha='right')
    text(.05,.895,sc['title'],28,weight='medium')
    text(.05,.832,sc['subtitle'],16,MUTED)
    d=data_at(idx,u)
    if idx in [0,1,2,4,5,6]:dot_plot(idx,u,d)
    elif idx==3:null_plot(u)
    elif idx==7:ci_plot(u)
    else:design_plot(u)
    if idx==0:
        metric(.71,'STUDY DESIGN','2 groups','Independent workers')
        metric(.54,'GROUP SIZE','20 each','One response per worker')
        metric(.37,'TASK','Correct report','Measured in seconds')
    elif idx==1:
        metric(.71,'BRIEFING − PRACTICE','48 − 42','Difference in mean time')
        metric(.52,'OBSERVED GAP','6 seconds','Positive favors practice')
        text(.755,.33,'Could sampling\nvariation explain\nthis difference?',18)
    elif idx==2:
        text(.755,.72,'WELCH TWO-SAMPLE t',13,MUTED)
        text(.755,.66,r'$t = \frac{\mathrm{mean\ difference}}{\mathrm{standard\ error}}$',23)
        text(.755,.53,r'$t = \frac{6.00}{2.53} = 2.37$',30)
        text(.755,.37,r'$SE=\sqrt{\frac{8^2}{20}+\frac{8^2}{20}}$',24)
        text(.755,.25,'SE is uncertainty in\nthe mean difference.',14,MUTED)
    elif idx==3:
        metric(.71,'OBSERVED TEST STATISTIC','t = 2.37','Two-sided comparison')
        metric(.53,'TAIL AREA','p = .023','About 2.3% in both tails')
        text(.755,.35,'H₀: μbriefing = μpractice',15)
        text(.755,.29,'At α = .05:\nreject equal means.',17)
    elif idx in [4,5,6]:
        # Numbers describe the observations on screen, including chapter starts.
        metric(.71,'MEAN DIFFERENCE',f"{d['gap']:.1f} seconds",f"n = {d['n']} per group")
        metric(.54,'STANDARD ERROR',f"{d['se']:.2f} seconds",f"Individual SD = {d['sd']:.0f} s")
        text(.755,.365,f"t = {d['t']:.2f}",27)
        text(.755,.30,'p '+pstr(d['p']),25)
    elif idx==7:
        metric(.71,'ESTIMATED ADVANTAGE','6.0 seconds','Faster with practice')
        metric(.53,'95% CONFIDENCE INTERVAL','0.9 to 11.1 s')
        text(.755,.36,'p = .023',24)
        text(.755,.29,'Statistical evidence\n≠ operational value',17)
    else:
        text(.755,.71,'BEFORE USING THE TEST',13,MUTED)
        text(.755,.65,'Independent workers / pairs\nContinuous outcome\nInspect groups / differences\nCheck skew and outliers',14,linespacing=1.6)
        text(.755,.42,'AFTER THE TEST',13,MUTED)
        text(.755,.36,'Report the difference,\nconfidence interval,\nand practical meaning.',17,linespacing=1.5)
    text(.05,.145,caption_wrap(sc['caption']),17,linespacing=1.5)
    text(.05,.036,'SYNTHETIC TEACHING DATA  ·  '+sc['note'],11,MUTED)
    text(.95,.036,f'{idx+1} / {len(SCENES)}',11,MUTED,ha='right')
    # Scene progress is a quiet strip and also makes holds visibly intentional.
    prog=fig.add_axes([.05,.012,.9,.005]);prog.set_xlim(0,126);prog.set_ylim(0,1);prog.axis('off')
    prog.axhspan(0,1,color=GRID);prog.fill_between([0,sc['start']+elapsed],0,1,color=BLUE)
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[:,:,:3].copy()

def previews():
    paths=[]
    for i,sc in enumerate(SCENES):
        path=OUT/f'qa_scene_{i+1}.png';Image.fromarray(draw(i,4)).save(path);paths.append(path)
    Image.open(paths[1]).save(OUT/'poster.png')
    sheet=Image.new('RGB',(1280,3*360),BG)
    for i,path in enumerate(paths[:6]):sheet.paste(Image.open(path).resize((640,360)),((i%2)*640,(i//2)*360))
    sheet.save(OUT/'qa_contact_sheet.png')
    sheet2=Image.new('RGB',(1280,720),BG)
    for j,i in enumerate([6,7,8]):sheet2.paste(Image.open(paths[i]).resize((640,360)),((j%2)*640,(j//2)*360))
    sheet2.save(OUT/'qa_contact_sheet_2.png')

def encode(ffmpeg='ffmpeg'):
    executable=shutil.which(str(ffmpeg))
    if executable is None:raise FileNotFoundError('FFmpeg was not found. Install it on PATH or supply --ffmpeg PATH.')
    cmd=[executable,'-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'RSCH650_T_Test_Animation.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for idx,sc in enumerate(SCENES):
        duration=sc['end']-sc['start'];cache={}
        for frame in range(duration*FPS):
            elapsed=frame/FPS
            # Full motion for the transition, then one refresh per second for progress.
            sample_t=elapsed if elapsed<2.6 else int(elapsed)
            if sample_t not in cache:
                arr=draw(idx,sample_t);cache={sample_t:arr.tobytes()}
            proc.stdin.write(cache[sample_t])
        print(f'Rendered chapter {idx+1}/{len(SCENES)}',flush=True)
    proc.stdin.close();assert proc.wait()==0
    print('Video complete',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Render the RSCH650 t-test lesson previews or 126-second video.')
    parser.add_argument('--output-dir',type=Path,default=SOURCE_DIR.parent)
    parser.add_argument('--ffmpeg',default='ffmpeg',help='FFmpeg executable name or path')
    parser.add_argument('--encode',action='store_true',help='Encode the video instead of writing previews')
    args=parser.parse_args()
    configure(args.output_dir)
    (OUT/'source').mkdir(parents=True,exist_ok=True)
    (OUT/'source'/'timeline.json').write_text(json.dumps(SCENES,indent=2)+'\n',encoding='utf-8',newline='\n')
    if args.encode:encode(args.ffmpeg)
    else:previews();print('Previews ready')
