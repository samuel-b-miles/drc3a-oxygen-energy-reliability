#!/usr/bin/env python3
"""Inventory every Ndosho device-load CSV in the pinned Aashika Nair source.

Preserves raw rows, zeros and conflicting timestamps. Normalized source times
remain timezone-naive until clock/timezone metadata are verified. No energy
integration or oxygen-production inference is performed here.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, re
from pathlib import Path
import numpy as np
import pandas as pd

COMMIT='c21987d8c0cb3d3653d6aad485ee32661e3a5565'
LABELS={
 'load_10L_concentrator.csv':'10 L/min concentrator',
 'load_5L_concentrator.csv':'5 L/min concentrator',
 'load_anesthesiology.csv':'anesthesiology load',
 'load_bloodanalyzer.csv':'blood analyzer load',
 'load_bloodfridge.csv':'blood refrigerator load',
 'load_neonatologie.csv':'neonatology aggregate load',
 'load_neonatology_concentrator.csv':'neonatology concentrator load',
 'load_phase1.csv':'phase 1 load', 'load_phase2.csv':'phase 2 load',
 'load_phase3.csv':'phase 3 load', 'load_recovery_room.csv':'recovery room load',
 'load_xray.csv':'X-ray load', 'total_load.csv':'total load (source label)',
}

def build(source: Path, public: Path, controlled: Path) -> dict:
    public.mkdir(parents=True,exist_ok=True);controlled.mkdir(parents=True,exist_ok=True)
    inventory=[]
    for n,(filename,label) in enumerate(LABELS.items(),1):
        path=source/'data'/filename
        df=pd.read_csv(path)
        df=df.rename(columns={'Power Factor':'PowerFactor','Power (W)':'Power(W)'})
        power_source_field='Power (W)'
        if filename=='total_load.csv':
            power_source_field='Total Power'
            def watts(value):
                m=re.fullmatch(r'\s*([+-]?[\d.]+)\s*(kW|W)\s*',str(value))
                return float(m[1])*(1000 if m[2]=='kW' else 1) if m else np.nan
            df['Power(W)']=df['Total Power'].map(watts)
        if not {'Time','PowerFactor','Power(W)'}.issubset(df.columns):
            raise ValueError(f'Unexpected schema in {filename}: {list(df.columns)}')
        t=pd.to_datetime(df['Time'],errors='coerce')
        power=pd.to_numeric(df['Power(W)'],errors='coerce')
        pf=pd.to_numeric(df['PowerFactor'],errors='coerce')
        sorted_time=t.dropna().sort_values().drop_duplicates()
        deltas=sorted_time.diff().dt.total_seconds().dropna()
        mode=float(deltas.mode().iloc[0]) if len(deltas) else None
        conflicts=(df.assign(parsed_time=t).groupby('parsed_time')[['PowerFactor','Power(W)']].nunique(dropna=False).max(axis=1)>1).sum()
        item={'collection_id':'N001','series_id':f'H{n:03d}','source_filename':filename,
              'source_url':f'https://github.com/astroash11/drc3/blob/{COMMIT}/data/{filename}',
              'download_url':f'https://raw.githubusercontent.com/astroash11/drc3/{COMMIT}/data/{filename}',
              'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_bytes':path.stat().st_size,
              'source_label':label,'label_status':'source_filename_physical_meter_and_deployment_not_verified',
              'rows':len(df),'first_time_source':str(t.min()),'last_time_source':str(t.max()),
              'source_timezone':'unverified','invalid_timestamps':int(t.isna().sum()),
              'duplicate_timestamp_extra_rows':int(t.dropna().duplicated().sum()),
              'conflicting_timestamps':int(conflicts),'non_increasing_source_steps':int((t.diff().dt.total_seconds()<=0).sum()),
              'modal_interval_seconds':mode,'median_interval_seconds':float(deltas.median()) if len(deltas) else None,
              'gaps_over_2x_modal_interval':int((deltas>2*mode).sum()) if mode else None,
              'largest_gap_seconds':float(deltas.max()) if len(deltas) else None,
              'zero_power_records':int(power.eq(0).sum()),'negative_power_records':int(power.lt(0).sum()),
              'nonfinite_power_records':int((~np.isfinite(power)).sum()),
              'power_factor_outside_0_1_records':int(((pf<0)|(pf>1)).sum()),
              'power_unit':'W','power_factor_unit':'dimensionless','overlaps_january_2025':bool(t.max()>=pd.Timestamp('2025-01-01') and t.min()<pd.Timestamp('2025-02-01'))}
        item['power_source_field']=power_source_field
        item['power_conversion']='parse explicit W/kW suffix; kW multiplied by 1000' if filename=='total_load.csv' else 'numeric source column labeled W'
        normalized=pd.DataFrame({'collection_id':'N001','series_id':item['series_id'],
               'source_row_number':np.arange(2,len(df)+2),'time_source':df['Time'],
               'time_parsed_naive':t,'timezone_status':'unverified','power_source':df['Total Power'] if filename=='total_load.csv' else df['Power(W)'],
               'power_W':power,'power_factor':pf})
        normalized.to_csv(controlled/f"N001_{item['series_id']}.csv.gz",index=False,compression={'method':'gzip','mtime':0})
        inventory.append(item)
    pd.DataFrame(inventory).drop(columns=['download_url']).to_csv(public/'series_inventory.csv',index=False)
    result={'source_repository':'https://github.com/astroash11/drc3','source_commit':COMMIT,
            'credit':'Aashika Nair (astroash11); device and circuit labels follow source filenames',
            'license_status':'no data license asserted; retain source attribution and obtain appropriate redistribution terms before bundling originals',
            'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,
            'series_count':len(inventory),'row_count':sum(x['rows'] for x in inventory),
            'normalized_row_count':sum(x['rows'] for x in inventory),
            'first_time_source':min(x['first_time_source'] for x in inventory),
            'last_time_source':max(x['last_time_source'] for x in inventory),
            'january_2025_device_load_overlap':any(x['overlaps_january_2025'] for x in inventory),
            'energy_policy':'do not sum W as Wh; future integration must use verified interval duration and exclude or bound gaps',
            'series':inventory}
    (public/'source_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    return {k:v for k,v in result.items() if k!='series'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-repo',type=Path,required=True)
    p.add_argument('--public-out',type=Path,default=Path('data/collections/ndosho/hopmeter'))
    p.add_argument('--controlled-out',type=Path,default=Path('outputs/private/ndosho/hopmeter'))
    a=p.parse_args();print(json.dumps(build(a.source_repo,a.public_out,a.controlled_out),indent=2))
