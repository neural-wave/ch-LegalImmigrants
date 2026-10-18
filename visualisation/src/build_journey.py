"""Chronological story assets. Measured evidence and conceptual panels stay labelled."""
import json
from pathlib import Path
from build_figures import setup, style, scope, box, arrow, THEMES
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
AUDIT = json.loads((ROOT/'data/calendar-experiment.json').read_text())

def journey(theme):
    fig,t,s=setup(theme,'The journey, not just the score')
    ax=fig.add_axes([.085,.20,.83,.54]); ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    stages=[('Observe','Errors reveal structure'),('Reconstruct','Historical rules'),('Extend','Tax hypotheses'),('Challenge','New evaluation data')]
    for i,(a,b) in enumerate(stages):
        x=.01+i*.25
        box(ax,x,.48,.21,.23,a,t,s,i==1)
        ax.text(x+.105,.34,b,ha='center',fontsize=7.3*s,color=t['muted'])
        if i<3: arrow(ax,(x+.215,.595),(x+.247,.595),t,s)
    ax.plot([.015,.47],[.13,.13],color=t['blue'],lw=3*s)
    ax.plot([.515,.97],[.13,.13],color=t['teal'],lw=3*s)
    ax.text(.24,.01,'Through #26: original tasks',ha='center',fontsize=8*s)
    ax.text(.745,.01,'Later: surprise tax task',ha='center',fontsize=8*s)
    scope(fig,'Team-confirmed focus · conceptual stages, not elapsed time',t,s)
    return fig

def rounding_counts(theme):
    fig,t,s=setup(theme,'One rule could not explain both eras')
    ax=fig.add_axes([.30,.23,.60,.48]);style(ax,t)
    labels=['Half-up everywhere','Truncate everywhere','Historical rules']
    nums=[2184,828,3011]
    ax.barh([2,1,0],nums,color=[t['blue'],t['blue'],t['teal']],height=.42)
    for y,n in zip([2,1,0],nums): ax.text(n+42,y,f'{n:,}',va='center',fontsize=10*s)
    ax.set(yticks=[2,1,0],yticklabels=labels,xlim=(0,3400),xticks=[0,1500,3019])
    ax.grid(axis='y',visible=False);ax.grid(axis='x',color=t['grid'])
    ax.set_xlabel('Exact matches out of 3,019',fontsize=8*s)
    scope(fig,'Measured t2 counterfactual · commit 8247f0f · train targets',t,s)
    return fig

def hidden_pots(theme):
    fig,t,s=setup(theme,'A missing row was not a missing holding')
    ax=fig.add_axes([.085,.21,.83,.52]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    for i,(label,col) in enumerate([('Fund A',t['blue']),('Fund B',t['blue']),('Fund C',t['teal'])]):
        x=.03+i*.25
        ax.add_patch(plt.Rectangle((x,.45),.18,.26,facecolor=t['soft'],edgecolor=col,lw=1.5*s))
        ax.text(x+.09,.58,label,ha='center',va='center',fontsize=10*s)
        ax.text(x+.09,.29,'Exported charge' if i<2 else 'Share rounds to zero',ha='center',fontsize=7.5*s,color=t['muted'])
    ax.annotate('',xy=(.71,.82),xytext=(.02,.82),arrowprops=dict(arrowstyle='|-|',color=t['teal'],lw=1.3*s))
    ax.text(.365,.91,'All holdings affect allocation',ha='center',fontsize=10*s)
    ax.text(.94,.57,'Replay\nfull state',ha='center',va='center',fontsize=11*s,color=t['teal'])
    arrow(ax,(.73,.58),(.82,.58),t,s)
    scope(fig,'Conceptual example · discovery recorded in historical notes',t,s)
    return fig

def masked(theme):
    fig,t,s=setup(theme,'A correct fix can leave the score unchanged')
    ax=fig.add_axes([.085,.20,.83,.55]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    cols=['Country','Base','Tax','Surcharge','Stamp','Date']
    for j,name in enumerate(cols): ax.text(.22+j*.105,.91,name,ha='center',fontsize=7*s,color=t['muted'])
    for i,(name,wrong,result) in enumerate([('Before',{1,5},'0'),('Fix base',{5},'0'),('Fix date',set(),'1')]):
        y=.67-i*.25
        ax.text(0,y+.06,name,va='center',fontsize=9*s)
        for j in range(6):
            ax.add_patch(plt.Rectangle((.18+j*.105,y),.08,.12,facecolor=t['red'] if j in wrong else t['teal'],alpha=.85))
            ax.text(.22+j*.105,y+.06,'×' if j in wrong else '✓',ha='center',va='center',fontsize=10*s,color=t['bg'])
        ax.text(.90,y+.06,result,ha='center',va='center',fontsize=14*s)
    ax.text(.90,.91,'Row score',ha='center',fontsize=7*s,color=t['muted'])
    scope(fig,'Invented correctness pattern · six-field payout exact-row metric',t,s)
    return fig

def isolated(theme):
    fig,t,s=setup(theme,'What did the calendar experiment change?')
    ax=fig.add_axes([.105,.24,.59,.47]);style(ax,t)
    labels=['Date','Base','Tax','Surcharge','Stamp','Country']
    vals=[AUDIT['columns_changed'][k] for k in ['remittance_date','taxable_base','withholding','surcharges','stamp_duty','country']]
    ax.barh(range(6),vals,color=t['teal'],height=.45)
    ax.set(yticks=range(6),yticklabels=labels,xlim=(0,185),xticks=[0,75,150]);ax.invert_yaxis()
    ax.grid(axis='y',visible=False);ax.grid(axis='x',color=t['grid'])
    for i,v in enumerate(vals):ax.text(v+4,i,str(v),va='center',fontsize=8*s)
    ax.set_xlabel('Payout rows changed',fontsize=8*s)
    fig.text(.76,.58,'0',fontsize=32*s,color=t['blue'])
    fig.text(.76,.47,'Annual rows\nchanged',fontsize=9*s,color=t['muted'])
    scope(fig,'Measured local toggle · upload #53 · 2,493 payout rows',t,s)
    return fig

def ledger(theme):
    fig,t,s=setup(theme,'The solution became a historical replay')
    ax=fig.add_axes([.085,.19,.83,.55]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    box(ax,.01,.44,.20,.22,'Events\nPrices / FX',t,s)
    box(ax,.32,.44,.30,.22,'Historical replay',t,s,True)
    box(ax,.74,.73,.24,.18,'Value / statement',t,s)
    box(ax,.74,.43,.24,.18,'Tax ledger',t,s,True)
    box(ax,.74,.13,.24,.18,'Residual checks',t,s)
    arrow(ax,(.22,.55),(.31,.55),t,s)
    for yy in [.82,.52,.22]:arrow(ax,(.63,.55),(.73,yy),t,s)
    ax.text(.47,.26,'Era · age · calendar · cents',ha='center',fontsize=8*s,color=t['muted'])
    scope(fig,'Conceptual architecture · discovery tools stay outside prediction',t,s)
    return fig

FIGURES={'05-journey':journey,'06-rounding-counterfactual':rounding_counts,
         '07-hidden-holdings':hidden_pots,'08-exact-row-masking':masked,
         '09-calendar-experiment':isolated,'10-historical-replay':ledger}

def main():
    for theme in THEMES:
        for name,fn in FIGURES.items():
            fig=fn(theme); folder=ROOT/theme
            for ext in (['svg','png','pdf'] if theme=='report' else ['svg','png']):
                fig.savefig(folder/f'{name}.{ext}',dpi=300 if theme=='report' else 120,facecolor=fig.get_facecolor())
            plt.close(fig)
    order=['05-journey','02-shared-engine','01-rounding-discovery','06-rounding-counterfactual','07-hidden-holdings','10-historical-replay','08-exact-row-masking','09-calendar-experiment','03-historical-tax-periods','04-sample-evidence']
    sheet=Image.new('RGB',(1600,5*480),'#e8edf2')
    for i,name in enumerate(order):
        im=Image.open(ROOT/'report'/f'{name}.png').convert('RGB');im.thumbnail((780,450))
        x=10+(i%2)*800;y=10+(i//2)*480
        sheet.paste(im,(x,y))
        ImageDraw.Draw(sheet).text((x+15,y+450),name,fill='#172331')
    sheet.save(ROOT/'journey-preview.png')
    cards=''.join(f'<article><h2>{i+1:02d}</h2><img src="report/{n}.svg" alt="{n}"><a href="report/{n}.pdf">Report PDF</a> · <a href="video/{n}.png">Video PNG</a></article>' for i,n in enumerate(order))
    (ROOT/'journey.html').write_text('<!doctype html><meta charset="utf-8"><title>Our investigation</title><style>body{max-width:1200px;margin:40px auto;background:#eef2f5;color:#172331;font:16px system-ui}header{padding:20px}main{display:grid;grid-template-columns:1fr 1fr;gap:20px}article{background:white;padding:18px;border-radius:12px}img{width:100%}h2{font-weight:400;color:#007f73}a{color:#2e62ad}</style><header><h1>Our investigation</h1><p>Ten scenes, ordered by the story. Measured evidence and conceptual illustrations are labelled in each figure.</p><p>Latest evaluation is provisional. See CAPTIONS.md and PROJECT_STORY.md for sources.</p></header><main>'+cards+'</main>')
    print('Created six new figures in both themes; ten-scene gallery ready.')

if __name__=='__main__':main()
