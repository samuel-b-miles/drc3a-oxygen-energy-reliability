#!/usr/bin/env python3
"""Descriptive event figure from released pseudonymous PowerWatch bucket exports."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Patch

INK='#203544';MUTED='#647684';TEAL='#168783';BLUE='#497E9E';ORANGE='#E2743E';GREY='#E4E9ED';PURPLE='#9C6695'

def build(source:Path,registry:Path,out:Path):
    out.mkdir(parents=True,exist_ok=True)
    df=pd.read_csv(source);df=df[df.metric.eq('voltage')].copy()
    df['time']=pd.to_datetime(df.time_utc,utc=True).dt.tz_convert('Africa/Kigali').dt.tz_localize(None)
    start=pd.Timestamp('2025-01-14');end=pd.Timestamp('2025-02-09')
    slots=pd.date_range(start,end,freq='2min',inclusive='left')
    if df.duplicated(['sensor_id','time']).any():raise ValueError('Resolve duplicate timestamps before plotting')
    series=df.pivot(index='time',columns='sensor_id',values='value').reindex(slots)
    reg=json.loads(registry.read_text());returned=[s for s in reg['sensors'] if s['sensor_id'] in series.columns]
    returned.sort(key=lambda s:(0 if s['site_id']=='S004' else 1,s['site_id'],s['sensor_id']))
    order=[s['sensor_id'] for s in returned]
    matrix=series[order].to_numpy().T
    states=np.zeros_like(matrix,dtype=int);states[np.isfinite(matrix)&(matrix<=23)]=1;states[np.isfinite(matrix)&(matrix>23)]=2
    states[np.isfinite(matrix)&(matrix<0)]=3
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':INK,'axes.labelcolor':INK,
                         'xtick.color':MUTED,'ytick.color':INK,'axes.spines.top':False,'axes.spines.right':False,
                         'pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(15.8,10.3),facecolor='white')
    fig.text(.05,.953,'Electricity during the January 2025 Goma event',fontsize=22,weight='bold')
    fig.text(.05,.922,'Ndosho paired series within the nine requested Goma sites · 14 January–8 February · CAT (UTC+2)',fontsize=11,color=MUTED)
    ax=fig.add_axes([.18,.61,.69,.235]);event_start=pd.Timestamp('2025-01-26');event_end=pd.Timestamp('2025-01-30')
    ax.axvspan(event_start,event_end,color='#FCEBD7',zorder=0)
    ax.axhline(230,color='#C0C9D0',lw=.8,ls='--');ax.axhline(23,color=ORANGE,lw=.75,ls=':')
    ax.plot(slots,series.M008,color=BLUE,lw=.55,label='M008 · clinic reference*',zorder=2)
    ax.plot(slots,series.M004,color=TEAL,lw=.7,label='M004 · laboratory reference*',zorder=3)
    ax.set_ylim(-5,280);ax.set_xlim(start,end);ax.set_ylabel('Exported voltage (V)',fontsize=11)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=4));ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.set_yticks([0,100,200,230]);ax.grid(axis='y',color='#EEF1F3');ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(0,1.04),ncol=2,fontsize=9)
    fig.text(.05,.871,'A  Ndosho',fontsize=12,weight='bold')
    ax.text(pd.Timestamp('2025-01-28'),265,'26–29 Jan: 96 generator-hours logged',ha='center',fontsize=9,color='#B96831',bbox={'fc':'white','ec':'none','alpha':.88,'pad':3})
    fig.text(.05,.552,'B  Measurement states across returned Goma series',fontsize=12,weight='bold')
    fig.text(.87,.552,'Bins with data',fontsize=9,color=MUTED,ha='center')
    heat=fig.add_axes([.18,.245,.69,.276])
    cmap=ListedColormap([GREY,ORANGE,TEAL,PURPLE]);norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
    heat.imshow(states,aspect='auto',interpolation='nearest',cmap=cmap,norm=norm,
                extent=[mdates.date2num(start),mdates.date2num(end),len(order)-.5,-.5])
    labels=[]
    for s in returned:
        labels.append(('Ndosho lab ref.*' if s['sensor_id']=='M004' else 'Ndosho clinic ref.*')+' · '+s['sensor_id'] if s['site_id']=='S004' else s['site_id']+' · '+s['sensor_id'])
    heat.set_yticks(range(len(order)),labels=labels,fontsize=9)
    heat.set_xlim(start,end);heat.xaxis_date();heat.xaxis.set_major_locator(mdates.DayLocator(interval=4));heat.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    heat.tick_params(axis='y',length=0,pad=9);heat.spines[['left','bottom']].set_visible(False)
    heat.axvline(event_start,color='#A55732',ls='--',lw=.8);heat.axvline(event_end,color='#A55732',ls='--',lw=.8)
    for i,sensor in enumerate(order):
        heat.text(1.025,i,f'{np.isfinite(matrix[i]).mean()*100:.1f}%',transform=heat.get_yaxis_transform(),va='center',ha='left',fontsize=9,color=MUTED)
    legend=[Patch(fc=TEAL,label='Observed >23 V'),Patch(fc=ORANGE,label='Observed ≤23 V'),Patch(fc=GREY,label='No measurement returned'),Patch(fc=PURPLE,label='Negative value: review')]
    fig.legend(handles=legend,loc='upper left',bbox_to_anchor=(.175,.218),ncol=4,frameon=False,fontsize=9.3,columnspacing=1.6)
    fig.text(.05,.153,'The register records four calendar days of generator operation and 600 L in fuel columns; fuel burn was not independently metered.',fontsize=10)
    fig.text(.05,.119,'*Circuit labels follow a placement reference; January 2025 placement and oxygen-serving connections still need confirmation.',fontsize=9.5,color=MUTED)
    fig.text(.05,.087,'Each pixel is a 120-second dashboard bucket. Mixed buckets prefer energized readings; gaps remain gaps. >23 V is a display screen,',fontsize=9.2,color=MUTED)
    fig.text(.05,.063,'not a concentrator operating threshold. Electrical measurements do not establish oxygen flow, PSA operation, or clinical outcomes.',fontsize=9.2,color=MUTED)
    fig.text(.05,.030,'Sources: nLine PowerWatch exports E003–E007; Ndosho register, ChCbNdosho 2025!A50:L54. Kyeshero source identity is unresolved.',fontsize=8.5,color=MUTED)
    for ext in ['png','pdf','svg']:fig.savefig(out/f'figure_1_event_descriptive.{ext}',dpi=180,facecolor='white')
    plt.close(fig)
    metrics=[]
    period=series.loc[(series.index>=event_start)&(series.index<event_end)]
    for sensor in order:
        x=period[sensor];metrics.append({'sensor_id':sensor,'expected_2min_bins':len(x),'bins_with_numeric_voltage':int(x.notna().sum()),
            'bins_above_23V':int(x.gt(23).sum()),'bins_at_or_below_23V':int(x.le(23).sum()),'missing_bins':int(x.isna().sum()),
            'percent_expected_bins_above_23V':round(100*x.gt(23).sum()/len(x),4),
            'minimum_observed_V':x.min(),'maximum_observed_V':x.max(),
            'interpretation':'bucket counts, not exact uptime, oxygen availability or duration of outages'})
    pd.DataFrame(metrics).to_csv(out/'event_bucket_summary.csv',index=False)
    (out/'figure_provenance.json').write_text(json.dumps({'source_readings_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'registry_sha256':hashlib.sha256(registry.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'event_boundaries':'generator-register calendar dates; grid-specific cutoff/restoration times not verified','records':len(df)},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('data/collections/goma/powerwatch/readings.csv.gz'))
    p.add_argument('--registry',type=Path,default=Path('data/collections/goma/powerwatch/series_registry.json'))
    p.add_argument('--output',type=Path,default=Path('outputs/event_figure'))
    a=p.parse_args();build(a.source,a.registry,a.output)
