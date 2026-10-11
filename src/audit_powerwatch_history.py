#!/usr/bin/env python3
"""Hash-verify bounded query exports and release Ndosho-only coverage evidence."""
from pathlib import Path
import csv, hashlib, json
ROOT=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    source=ROOT/'data/raw/private/ndosho/powerwatch/history_manifest.json'
    manifest=json.loads(source.read_text());registry=json.loads((ROOT/'config/private/powerwatch_registry.json').read_text())
    aliases={x['source_sensor_serial'].upper():x['sensor_id'] for x in registry['sensors'] if x['site_id']=='S004'}
    out=ROOT/'data/collections/ndosho/powerwatch';out.mkdir(parents=True,exist_ok=True)
    public_exports=[]
    for export in manifest['exports']:
        path=ROOT/export['relative_path']
        if digest(path)!=export['sha256']:raise ValueError('Query export hash mismatch')
        with path.open(newline='',encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
        kept=[]
        for line,row in enumerate(rows,2):
            if export['kind']=='deployment' and row['site_id']!='ch cbca bethesda ndosho':continue
            alias=row['source_series_id'].upper()
            if alias not in aliases:raise ValueError('Unmapped Ndosho alias')
            item={'sensor_id':aliases[alias],'source_export_id':export['export_id'],'source_csv_line':line}
            fields={'deployment':['deployment_start_source','deployment_end_source','deployment_time_type'],
                    'installation_summary':['measurement_time_type','first_time_source','last_time_source','raw_rows','observed_2min_buckets'],
                    'latest_summary':['latest_time_source']}[export['kind']]
            item.update({x:row[x] for x in fields});kept.append(item)
        if kept:
            target=out/(export['kind']+'.csv')
            with target.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(kept[0]));w.writeheader();w.writerows(kept)
        public_exports.append({k:v for k,v in export.items() if k not in {'relative_path','source_original_filename'}})
    release={k:v for k,v in manifest.items() if k!='exports'};release['exports']=public_exports
    release['pipeline_sha256']=digest(Path(__file__));release['outputs_sha256']={p.name:digest(p) for p in out.glob('*_summary.csv')}
    release['outputs_sha256']['deployment.csv']=digest(out/'deployment.csv')
    (out/'history_query_manifest.json').write_text(json.dumps(release,indent=2)+'\n')
    return release
if __name__=='__main__':print(json.dumps({'exports':len(build()['exports'])}))
