"""Portable five-plot interface. Inputs are prepared, disclosure-reviewed summaries.

Demo data are invented. This module does not implement upstream survey coding.
"""
from pathlib import Path
import argparse, json, math

def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)

def validate(bundle):
    for key in ('calendar','voltage','devices','distribution','damage'):
        if not isinstance(bundle.get(key),list) or not bundle[key]:raise ValueError(f'{key}: nonempty list required')
    from datetime import datetime
    for r in bundle['calendar']:
        start,end=map(datetime.fromisoformat,(r['start'],r['end']))
        if end<=start or not isinstance(r['reported'],bool):raise ValueError('calendar: ordered interval and boolean required')
    cadence=bundle.get('voltage_cadence_seconds')
    if not finite(cadence) or cadence<=0:raise ValueError('voltage: positive cadence required')
    seen=set()
    for r in bundle['voltage']:
        stamp=datetime.fromisoformat(r['time'])
        if stamp.tzinfo is None:raise ValueError('voltage: explicit timezone required')
        key=(r['series'],stamp)
        if key in seen:raise ValueError('voltage: duplicate series/time')
        seen.add(key)
        if r['volts'] is not None and (not finite(r['volts']) or r['volts']<0):raise ValueError('voltage: nonnegative or null required')
    for series in set(r['series'] for r in bundle['voltage']):
        times=sorted(datetime.fromisoformat(r['time']) for r in bundle['voltage'] if r['series']==series)
        if any((b-a).total_seconds()!=cadence for a,b in zip(times,times[1:])):raise ValueError('voltage: missing cadence slot; supply null')
    for r in bundle['devices']:
        for k in ('beds','concentrators','oximeters'):
            if not finite(r[k]) or r[k]<0:raise ValueError('devices: nonnegative values required')
        if r['beds']==0 and (r['concentrators'] or r['oximeters']):raise ValueError('devices: positive devices with zero beds unresolved')
    for r in bundle['distribution']:
        if r['uptime_pct'] is not None and (not finite(r['uptime_pct']) or not 0<=r['uptime_pct']<=100):raise ValueError('distribution: invalid uptime')
        if not finite(r['capacity_lpm']) or r['capacity_lpm']<0:raise ValueError('distribution: nonnegative capacity required')
    for r in bundle['damage']:
        for group in ('exposed','reference'):
            n,y=r[group+'_n'],r[group+'_yes']
            if not isinstance(n,int) or not isinstance(y,int) or n<=0 or not 0<=y<=n:raise ValueError('damage: invalid numerator/denominator')
    return bundle

def ecdf(values):
    values=sorted(x for x in values if x is not None)
    return values,[(i+1)/len(values) for i in range(len(values))]

def device_rate(count,beds):
    return 100*count/beds if beds else None

def build(bundle,out,per_bed=False):
    validate(bundle)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from datetime import datetime
    from matplotlib.backends.backend_pdf import PdfPages
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    with PdfPages(out/'five_plots.pdf') as pdf:
        def save(fig,name):
            fig.tight_layout();fig.savefig(out/(name+'.png'),dpi=120);pdf.savefig(fig);plt.close(fig)
        fig,ax=plt.subplots(figsize=(10,5))
        labels=list(dict.fromkeys(r['label'] for r in bundle['calendar']))
        for r in bundle['calendar']:
            lo,hi=map(datetime.fromisoformat,(r['start'],r['end']))
            ax.barh(labels.index(r['label']),hi-lo,left=lo,color='#478aad' if r['reported'] else '#cbd1d5')
        ax.set_yticks(range(len(labels)),labels);ax.set_title('Reporting calendar — presence is not uptime');ax.xaxis_date();save(fig,'01_calendar')
        fig,ax=plt.subplots(figsize=(10,5))
        for series in dict.fromkeys(r['series'] for r in bundle['voltage']):
            rows=sorted((r for r in bundle['voltage'] if r['series']==series),key=lambda r:r['time'])
            ax.plot([datetime.fromisoformat(r['time']) for r in rows],[np.nan if r['volts'] is None else r['volts'] for r in rows],label=series)
        ax.set_ylabel('Voltage (V)');ax.set_title('Monitored voltage — null slots remain gaps');ax.legend();save(fig,'02_voltage')
        fig,ax=plt.subplots(figsize=(10,5));rows=bundle['devices'];x=np.arange(len(rows))
        for offset,key in [(-.18,'concentrators'),(.18,'oximeters')]:
            vals=[device_rate(r[key],r['beds']) if per_bed else r[key] for r in rows]
            ax.bar(x+offset,[np.nan if v is None else v for v in vals],width=.36,label=key)
        ax.set_xticks(x,[r['label'] for r in rows]);ax.set_ylabel('Reported devices per 100 matched beds' if per_bed else 'Reported device count');ax.legend();save(fig,'03_devices')
        fig,axes=plt.subplots(1,2,figsize=(10,5))
        for group in dict.fromkeys(r['class'] for r in bundle['distribution']):
            rows=[r for r in bundle['distribution'] if r['class']==group]
            for ax,key in zip(axes,('uptime_pct','capacity_lpm')):
                xs,ys=ecdf([r[key] for r in rows]);ax.step(xs,ys,where='post',label=f'{group} n={len(xs)}')
        axes[0].set_xlabel('Recall uptime (%)');axes[1].set_xlabel('Nominal capacity (L/min)');axes[1].set_xscale('symlog',linthresh=1)
        for ax in axes:ax.set_ylabel('Within-class cumulative share');ax.legend();ax.set_ylim(0,1.05)
        save(fig,'04_distributions')
        fig,ax=plt.subplots(figsize=(10,5));rows=bundle['damage'];x=np.arange(len(rows))
        for offset,group in [(-.18,'exposed'),(.18,'reference')]:
            ax.bar(x+offset,[100*r[group+'_yes']/r[group+'_n'] for r in rows],width=.36,label=group)
        ax.set_xticks(x,[r['contrast'] for r in rows]);ax.set_ylabel('Reported outcome prevalence (%)');ax.set_ylim(0,100);ax.legend();save(fig,'05_damage')
    return out/'five_plots.pdf'

def synthetic_bundle():
    """Invented values and labels, unrelated to any research cohort."""
    return {'voltage_cadence_seconds':120,'calendar':[{'label':'Demo source A','start':'2000-01-01','end':'2000-01-03','reported':True},{'label':'Demo source A','start':'2000-01-03','end':'2000-01-04','reported':False}],
    'voltage':[{'series':'Demo series A','time':f'2000-01-01T00:0{i}:00+00:00','volts':v} for i,v in zip((0,2,4),(210,None,220))],
    'devices':[{'label':'Demo ward A','beds':20,'concentrators':2,'oximeters':3},{'label':'Demo ward B','beds':0,'concentrators':0,'oximeters':0}],
    'distribution':[{'class':'Demo class A','uptime_pct':u,'capacity_lpm':c} for u,c in [(None,0),(20,0),(80,10)]],
    'damage':[{'contrast':'Demo contrast A','exposed_n':10,'exposed_yes':2,'reference_n':12,'reference_yes':5}]}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--per-bed',action='store_true');a=p.parse_args()
    print(build(json.loads(a.input.read_text()) if a.input else synthetic_bundle(),a.output,a.per_bed))
