"""Native IEEE-column figures: compact geometry, readable type, no slide margins."""
import json
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from datetime import date

C={'ink':'#172331','muted':'#566572','teal':'#007f73','blue':'#2e62ad','red':'#b44747','soft':'#eff3f6','grid':'#e0e6eb'}
OUT=ROOT.parent/'report/images'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'text.color':C['ink'],
 'axes.labelcolor':C['muted'],'xtick.color':C['muted'],'ytick.color':C['muted'],
 'pdf.fonttype':42,'svg.fonttype':'none'})

def canvas(height):
    fig=plt.figure(figsize=(3.48,height),facecolor='white')
    ax=fig.add_axes([.025,.035,.95,.93]);ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    return fig,ax

def label(ax,x,y,text,size=8,color='ink',**kw):
    return ax.text(x,y,text,fontsize=size,color=C.get(color,color),**kw)

def tile(ax,x,y,w,h,text,accent=False,size=8):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.006,rounding_size=.018',lw=.6,
        edgecolor=C['teal'] if accent else C['grid'],facecolor='#edf7f5' if accent else C['soft']))
    label(ax,x+w/2,y+h/2,text,size,'teal' if accent else 'ink',ha='center',va='center')

def arrow(ax,start,end):
    ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'-|>','lw':.8,'color':C['muted'],'mutation_scale':8})

def process():
    fig,ax=canvas(1.06)
    for i,(a,b) in enumerate([('Compare','Find errors'),('Explain','Inspect groups'),('Test','Isolate a rule'),('Verify','Check outputs')]):
        x=.015+i*.25
        tile(ax,x,.44,.215,.39,a,i==2)
        label(ax,x+.107,.23,b,7,'muted',ha='center')
        if i<3:arrow(ax,(x+.22,.635),(x+.247,.635))
    return fig

def rounding():
    data=json.loads((ROOT/'data/rounding-evidence.json').read_text())
    fig=plt.figure(figsize=(3.48,1.97),facecolor='white')
    ax=fig.add_axes([.145,.23,.80,.63]);xs=[date.fromisoformat(r['quarter']) for r in data['quarters']]
    for key,col,ls in [('half_up_everywhere','red','--'),('historical','teal','-')]:
        ax.plot(xs,[100*r[key]/r['n'] for r in data['quarters']],color=C[col],ls=ls,lw=1.3)
    cut=date.fromisoformat(data['conversion']);ax.axvline(cut,color=C['muted'],lw=.7)
    ax.text(date(2008,8,1),105,'Aug 2007',fontsize=7,color=C['muted'])
    ax.text(date(1994,1,1),75,'Uniform half-up',fontsize=7.5,color=C['red'])
    ax.text(date(2011,1,1),16,'Historical',fontsize=7.5,color=C['teal'])
    ax.set(ylim=(-4,115),yticks=[0,50,100],ylabel='Mismatch (%)',xlabel='Application year')
    ax.xaxis.set_major_locator(mdates.YearLocator(10));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.tick_params(length=0,labelsize=7,pad=3);ax.grid(axis='y',lw=.5,color=C['grid'])
    for sp in ax.spines.values():sp.set_visible(False)
    ax.yaxis.label.set_size(7.5);ax.xaxis.label.set_size(7.5)
    return fig

def hidden():
    fig,ax=canvas(1.21)
    for i,name in enumerate(['Fund A','Fund B','Fund C']):
        x=.025+i*.335
        tile(ax,x,.34,.275,.36,name,i==2)
        label(ax,x+.137,.15,'Charge row' if i<2 else 'Zero share: no row',7,'muted',ha='center')
    ax.plot([.04,.97],[.88,.88],color=C['teal'],lw=1)
    label(ax,.50,.97,'Allocate over all held funds',8,'teal',ha='center')
    return fig

def solution():
    fig,ax=canvas(1.27)
    tile(ax,.015,.36,.235,.35,'Events\nPrices / FX',size=7.5)
    tile(ax,.365,.36,.275,.35,'Historical\nreplay',True,size=8)
    arrow(ax,(.26,.535),(.35,.535))
    for y,text in [(.72,'Values'),(.38,'Tax ledger'),(.04,'Residuals')]:
        tile(ax,.77,y,.21,.25,text,size=7.5)
        arrow(ax,(.65,.535),(.755,y+.125))
    label(ax,.49,.11,'Era / calendar / cents',7,'muted',ha='center')
    return fig

def masking():
    fig,ax=canvas(1.43)
    cols=['Ctry','Base','Tax','Extra','Duty','Date']
    for j,col in enumerate(cols):label(ax,.265+j*.10,.88,col,7,'muted',ha='center')
    label(ax,.935,.88,'Score',7,'muted',ha='center')
    for i,(name,wrong,score) in enumerate([('Before',{1,5},'0'),('Fix base',{5},'0'),('Fix date',set(),'1')]):
        y=.63-i*.25;label(ax,.01,y+.07,name,8,va='center')
        for j in range(6):
            x=.225+j*.10;ax.add_patch(plt.Rectangle((x,y),.08,.15,facecolor=C['red'] if j in wrong else C['teal'],lw=0))
            label(ax,x+.04,y+.075,'×' if j in wrong else '✓',9,'white',ha='center',va='center')
        label(ax,.935,y+.075,score,10,ha='center',va='center')
    return fig

def calendar():
    a=json.loads((ROOT/'data/calendar-experiment.json').read_text())
    fig,ax=canvas(1.14)
    for x,value,name,color in [(.02,a['date_changes'],'Payout dates','teal'),(.36,a['other_field_changes'],'Other fields','muted'),(.70,a['annual_row_changes'],'Annual rows','muted')]:
        tile(ax,x,.25,.28,.65,'',color=='teal')
        label(ax,x+.14,.65,str(value),20,color,ha='center',va='center')
        label(ax,x+.14,.38,name,7.5,'muted',ha='center',va='center')
    return fig

FIGURES={'paper-01-method':process,'paper-02-era':rounding,'paper-03-holdings':hidden,
         'paper-04-replay':solution,'paper-05-masking':masking,'paper-06-calendar':calendar}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for name,draw in FIGURES.items():
        fig=draw()
        for ext in ['pdf','png','svg']:fig.savefig(OUT/f'{name}.{ext}',dpi=300,facecolor='white')
        plt.close(fig)
    print('Built six native-column figures (PDF, SVG, PNG).')

if __name__=='__main__':main()
