"""Minimal report/video figures. Explanations and provenance live in CAPTIONS.md.
Report: vector PDF/SVG and PNG. Video: 1920 x 1080 PNG/SVG.
"""
from datetime import date
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from PIL import Image

ERA = json.loads((ROOT / 'data/rounding-evidence.json').read_text())
SCORES = json.loads((ROOT / 'data/sample-rescores.json').read_text())
THEMES = {
    'report': dict(bg='#ffffff', fg='#172331', muted='#596775', grid='#e4e9ee', soft='#f1f4f6',
                   red='#c44545', blue='#2e62ad', teal='#007f73', size=(7.16, 4.15), scale=1),
    'video': dict(bg='#0d1522', fg='#edf2f7', muted='#a5b3c4', grid='#263448', soft='#182538',
                  red='#ed8585', blue='#9dbfea', teal='#70d5bd', size=(16, 9), scale=2.05),
}


def setup(theme, title):
    t = THEMES[theme]; s = t['scale']
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':9*s,
        'text.color':t['fg'], 'axes.labelcolor':t['muted'], 'xtick.color':t['muted'],
        'ytick.color':t['muted'], 'svg.fonttype':'none', 'pdf.fonttype':42})
    fig = plt.figure(figsize=t['size'], facecolor=t['bg'])
    fig.text(.085, .88, title, fontsize=17*s, weight='normal')
    return fig, t, s


def scope(fig, text, t, s):
    fig.text(.085, .055, text, fontsize=7.2*s, color=t['muted'])


def style(ax, t):
    ax.set_facecolor(t['bg'])
    for spine in ax.spines.values(): spine.set_visible(False)
    ax.tick_params(length=0, pad=7)
    ax.grid(axis='y', color=t['grid'], lw=.65)
    ax.set_axisbelow(True)


def rounding(theme):
    fig,t,s = setup(theme, 'A hidden system switch')
    ax = fig.add_axes([.105,.22,.81,.50]); style(ax,t)
    xs = [date.fromisoformat(q['quarter']) for q in ERA['quarters']]
    for key,color,linestyle in [('half_up_everywhere',t['red'],'--'),('historical',t['teal'],'-')]:
        ax.plot(xs,[100*q[key]/q['n'] for q in ERA['quarters']],color=color,lw=2*s,ls=linestyle)
    cut = date.fromisoformat(ERA['conversion'])
    ax.axvline(cut,color=t['muted'],lw=.75*s,alpha=.7)
    ax.text(mdates.date2num(cut)+180,105,'Aug 2007',fontsize=8*s,color=t['muted'])
    ax.text(mdates.date2num(date(1995,1,1)),85,'One rounding rule',fontsize=9*s,color=t['fg'])
    ax.text(mdates.date2num(date(2012,1,1)),13,'Historical rules',fontsize=9*s,color=t['fg'])
    ax.set(ylim=(-5,112),yticks=[0,50,100],yticklabels=['0','50','100'])
    ax.xaxis.set_major_locator(mdates.YearLocator(10,month=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.text(-.025,1.12,'Mismatch (%)',transform=ax.transAxes,fontsize=8*s,color=t['muted'])
    ax.set_xlabel('Application year',fontsize=8*s,labelpad=10)
    scope(fig,'Train targets · n = 3,019',t,s)
    return fig


def arrow(ax,a,b,t,s):
    ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',color=t['muted'],lw=1*s,mutation_scale=9*s))


def box(ax,x,y,w,h,text,t,s,accent=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008,rounding_size=0.012',
                              facecolor=t['soft'],linewidth=0))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=10*s,
            color=t['teal'] if accent else t['fg'],weight='normal')


def engine(theme):
    fig,t,s=setup(theme,'From errors to rules')
    ax=fig.add_axes([.085,.18,.83,.55]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    ax.text(0,.96,'Discovery',fontsize=8*s,color=t['muted'])
    for i,(x,label) in enumerate([(0,'Compare'),(.26,'Explain'),(.52,'Test'),(.78,'Verify')]):
        box(ax,x,.62,.21,.22,label,t,s)
        if i<3:arrow(ax,(x+.22,.73),(x+.25,.73),t,s)
    ax.text(0,.43,'Execution',fontsize=8*s,color=t['muted'])
    box(ax,0,.08,.23,.23,'Legacy data',t,s)
    box(ax,.36,.08,.28,.23,'Shared rules',t,s,True)
    box(ax,.77,.08,.22,.23,'Outputs',t,s)
    arrow(ax,(.24,.195),(.35,.195),t,s)
    arrow(ax,(.65,.195),(.76,.195),t,s)
    arrow(ax,(.885,.61),(.885,.49),t,s)
    arrow(ax,(.885,.49),(.50,.34),t,s)
    scope(fig,'Architecture schematic',t,s)
    return fig


def tax_periods(theme):
    fig,t,s=setup(theme,'Timing changes the tax')
    ax=fig.add_axes([.12,.25,.52,.46]);style(ax,t)
    values=[80,-20,100]
    ax.axhline(0,color=t['muted'],lw=.8*s)
    bars=ax.bar([0,1,2],values,width=.43,color=[t['blue'],t['red'],t['blue']],zorder=3)
    for bar,v in zip(bars,values):
        ax.text(bar.get_x()+bar.get_width()/2,v+(7 if v>0 else -7),f'{v:+}',ha='center',
                va='bottom' if v>0 else 'top',fontsize=11*s,color=t['fg'])
    ax.set(ylim=(-48,130),yticks=[],xticks=[0,1,2],xticklabels=['12.5%','20%','26%'])
    ax.grid(False)
    ax.text(-.12,1.1,'Gain',transform=ax.transAxes,fontsize=8*s,color=t['muted'])
    ax.set_xlabel('Rate in each period',fontsize=8*s,labelpad=10)
    fig.text(.76,.62,'32',fontsize=29*s,color=t['teal'],weight='normal')
    fig.text(.76,.55,'Period tax',fontsize=8*s,color=t['fg'])
    fig.text(.76,.36,'41.60',fontsize=24*s,color=t['muted'],weight='normal')
    fig.text(.76,.29,'Final-rate tax',fontsize=8*s,color=t['fg'])
    scope(fig,'Illustrative · invented gain units',t,s)
    return fig


def samples(theme):
    fig,t,s=setup(theme,'Released-sample fit')
    ax=fig.add_axes([.105,.22,.81,.51]);style(ax,t)
    records=SCORES['snapshots']
    for key,color,marker in [('payout',t['teal'],'o'),('annual',t['blue'],'s')]:
        ys=[100*r[key][0]/r[key][1] for r in records]
        ax.plot(range(len(records)),ys,color=color,marker=marker,ms=4*s,lw=1.8*s)
        y=105 if key=='payout' else 92
        end=records[-1][key]
        label=f"{'Payout' if key=='payout' else 'Annual'} {end[0]}/{end[1]}"
        ax.annotate(label,xy=(4,100),xytext=(4.25,y),fontsize=8*s,color=t['fg'],va='center',
                    arrowprops=dict(arrowstyle='-',color=color,lw=.8*s))
    ax.set(ylim=(0,115),yticks=[0,50,100],yticklabels=['0','50','100'],xlim=(-.2,5.5),
           xticks=range(len(records)),xticklabels=[f"#{r['upload']}" for r in records])
    ax.text(-.025,1.08,'Exact rows (%)',transform=ax.transAxes,fontsize=8*s,color=t['muted'])
    ax.set_xlabel('Upload',fontsize=8*s,labelpad=10)
    scope(fig,'Development samples · not an independent holdout',t,s)
    return fig


FIGURES={'01-rounding-discovery':rounding,'02-shared-engine':engine,
         '03-historical-tax-periods':tax_periods,'04-sample-evidence':samples}


def main():
    for theme in THEMES:
        folder=ROOT/theme;folder.mkdir(exist_ok=True)
        for name,draw in FIGURES.items():
            fig=draw(theme)
            fig.savefig(folder/(name+'.svg'),facecolor=fig.get_facecolor())
            fig.savefig(folder/(name+'.png'),dpi=300 if theme=='report' else 120,facecolor=fig.get_facecolor())
            if theme=='report':
                fig.savefig(folder/(name+'.pdf'),facecolor=fig.get_facecolor(),
                            metadata={'Title':name,'Subject':'See visualisation/CAPTIONS.md for interpretation and provenance.'})
            plt.close(fig)
    sheet=Image.new('RGB',(1920,1080),THEMES['video']['bg'])
    for i,name in enumerate(FIGURES):
        im=Image.open(ROOT/'video'/(name+'.png')).convert('RGB');im.thumbnail((960,540))
        sheet.paste(im,((i%2)*960,(i//2)*540))
    sheet.save(ROOT/'preview.png')
    print('Rebuilt 4 simplified figures in report and video formats.')


if __name__=='__main__':main()
