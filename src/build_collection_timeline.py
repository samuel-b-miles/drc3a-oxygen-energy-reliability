#!/usr/bin/env python3
"""Facility-grouped chronology distinguishes source spans from confirmed coverage."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib.patches import Patch

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/data_timeline'
BLUE='#497E9E';TEAL='#168783';GOLD='#B88936';PURPLE='#8570A5';INK='#203544';GREY='#647684'

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    h=pd.read_csv(ROOT/'data/collections/ndosho/hopmeter/series_inventory.csv')
    survey=json.loads((ROOT/'outputs/drc2_failure_audit/run_audit.json').read_text())
    rows=[
      {'group':'Ndosho','dataset':'Historical grid and generator ledger','start':'2020-01-01','end':'2023-12-31','status':'coarse date range; mixed date formats','kind':'records','source':'data/collections/ndosho/historical/source_manifest.json'},
      {'group':'Ndosho','dataset':'2023 generator register','start':'2023-01-01','end':'2023-12-31','status':'year confirmed; day/month audit pending','kind':'records','source':'data/collections/ndosho/generator_register/source_manifest.json'},
      {'group':'Ndosho','dataset':'PowerWatch paired monitoring target','start':'2022-05-27','end':'2026-10-11','status':'both deployed May 2022; intervening coverage unverified','kind':'target','source':'data/collections/ndosho/powerwatch/coverage_request.json'},
      {'group':'Ndosho','dataset':'PowerWatch paired installation week','start':'2022-05-27','end':'2022-06-03','status':'both series returned; UTC measurement timestamps','kind':'telemetry','source':'data/collections/ndosho/powerwatch/installation_summary.csv'},
      {'group':'Ndosho','dataset':'PowerWatch current-week export','start':'2026-10-05','end':'2026-10-11','status':'one series returned; current pair not confirmed','kind':'telemetry','source':'data/collections/ndosho/powerwatch/current_week/export_manifest.json'},
      {'group':'Ndosho','dataset':'PowerWatch paired event exports','start':'2025-01-14','end':'2025-02-09','status':'two series exported; missing bins retained','kind':'telemetry','source':'data/collections/goma/powerwatch/export_manifest.json'},
      {'group':'Ndosho','dataset':'2024–2025 generator and fuel register','start':'2024-12-26','end':'2025-03-01','status':'dated manual entries plus separate model estimates','kind':'records','source':'data/collections/ndosho/generator_register/source_manifest.json'},
    ]
    for _,x in h.iterrows():rows.append({'group':'Ndosho','dataset':f"HOPmeter {x.series_id} · {x.source_label}",'start':x.first_time_source,'end':x.last_time_source,'status':'source timestamp span; gaps and clock zone unverified','kind':'telemetry','source':'data/collections/ndosho/hopmeter/series_inventory.csv'})
    rows.extend([
      {'group':'Comparative data','dataset':'Valentin ward assessment','start':'2024-10-08','end':'2024-11-04','status':'17 dated facility visits; Ndosho 15 Oct 2024','kind':'survey','source':'Valentin thesis, Table 34, printed p. 102'},
      {'group':'Comparative data','dataset':'Goma event exports · nine requested sites','start':'2025-01-14','end':'2025-02-09','status':'13 returned series; census of all Goma sensors unverified','kind':'telemetry','source':'data/collections/goma/powerwatch/export_manifest.json'},
      {'group':'Comparative data','dataset':'DRC2 survey · submission timestamps','start':survey['submission_time_start'],'end':survey['submission_time_end'],'status':'565 submissions / 491 facilities; interview dates unverified','kind':'survey','source':'outputs/drc2_failure_audit/run_audit.json'},
      {'group':'Ndosho follow-up','dataset':'Retrospective field interview','start':'2026-01-27','end':'2026-01-27','status':'account recorded in 2026; PSA installation date unresolved','kind':'interview','source':'https://docs.google.com/document/d/1TKk1lK1sBN_XpJI80o6OH_NnTJVLZYoZYsAHRBCoRZ8/edit'},
    ])
    pd.DataFrame(rows).to_csv(OUT/'dataset_time_mapping.csv',index=False)
    colors={'telemetry':BLUE,'records':GOLD,'survey':TEAL,'interview':PURPLE,'target':'#C0CBD3'}
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'text.color':INK,'xtick.color':GREY,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig=plt.figure(figsize=(18,15),facecolor='white')
    fig.text(.035,.955,'DRC3a data collection and monitoring coverage',fontsize=24,weight='bold')
    fig.text(.035,.926,'All Ndosho electricity, generator, fuel and device-load records belong to one facility collection.',fontsize=12,color=GREY)
    ax=fig.add_axes([.29,.20,.36,.66]);ax.set_xlim(pd.Timestamp('2019-11-01'),pd.Timestamp('2026-12-31'));ax.set_ylim(-1,len(rows));ax.invert_yaxis();ax.set_yticks([])
    ax.xaxis.set_major_locator(md.YearLocator());ax.xaxis.set_major_formatter(md.DateFormatter('%Y'));ax.grid(axis='x',color='#E4E9ED',lw=.8)
    ax.spines[['left','top','right']].set_visible(False)
    for i,r in enumerate(rows):
        if i%2==0:ax.axhspan(i-.42,i+.42,color='#F6F8FA',zorder=0)
        a,b=md.date2num(pd.Timestamp(r['start'])),md.date2num(pd.Timestamp(r['end']))
        coarse=r['kind']=='target' or 'coarse' in r['status'] or 'day/month' in r['status']
        if a==b:ax.plot(a,i,'D',color=colors[r['kind']],ms=6,zorder=4)
        else:ax.barh(i,b-a,left=a,height=.26,facecolor='#F6F8FA' if coarse else colors[r['kind']],edgecolor=colors[r['kind']],hatch='////' if coarse else None,zorder=2)
        ax.text(-.027,i,r['dataset'],transform=ax.get_yaxis_transform(),ha='right',va='center',fontsize=9.8)
        ax.text(1.03,i,r['status'],transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=9,color=GREY)
    ax.axvline(pd.Timestamp('2025-01-27'),color='#E2743E',ls='--',lw=1)
    ax.text(pd.Timestamp('2025-01-27'),-1.6,'Jan 2025 event',ha='center',fontsize=9,color='#C46636')
    fig.text(.035,.881,'Ndosho collection',fontsize=13,weight='bold');fig.text(.665,.881,'Date or coverage qualification',fontsize=10,weight='bold',color=GREY)
    for i in range(1,len(rows)):
        if rows[i]['group']!=rows[i-1]['group']:ax.axhline(i-.5,color='#D4DDE3',lw=1)
    fig.legend(handles=[Patch(fc=BLUE,label='Electrical telemetry'),Patch(fc=GOLD,label='Operating records'),Patch(fc=TEAL,label='Survey / assessment'),Patch(fc=PURPLE,label='Interview'),Patch(fc='white',ec='#94A4AF',hatch='////',label='Requested or coarse span')],loc='upper left',bbox_to_anchor=(.033,.168),ncol=5,frameon=False,fontsize=10)
    fig.text(.035,.116,'Bars show file or study spans, not continuous coverage. HOPmeter device files end by 18 Jan 2024; none overlap the Jan 2025 event.',fontsize=11,weight='bold')
    fig.text(.035,.082,'Both PowerWatch sensors returned in May–June 2022 and January–February 2025. October 2026 returns one; full paired history remains unverified.',fontsize=10,color=GREY)
    fig.text(.035,.052,'The DRC2 survey is later than the event. Generator hours, voltage, device power, delivered oxygen and clinical outcomes remain distinct evidence layers.',fontsize=10,color=GREY)
    fig.text(.035,.025,'Sources and exact timestamps: dataset_time_mapping.csv and collection manifests. Ward table includes one separate January 2024 date that remains unverified.',fontsize=9,color=GREY)
    for ext in ['png','pdf','svg']:fig.savefig(OUT/f'drc3a_collection_timeline.{ext}',dpi=160,facecolor='white')
    plt.close(fig)

if __name__=='__main__':build()
