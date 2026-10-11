#!/usr/bin/env python3
"""Verify new release hashes and scan published data for controlled identifiers."""
from pathlib import Path
import argparse,csv,gzip,hashlib,json,re,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
AREAS=['data/collections/ndosho','data/collections/goma','outputs/drc2_failure_audit','outputs/event_figure','outputs/data_timeline']
INVENTORY=ROOT/'data/collections/release_inventory.json'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def texts(path):
    if path.suffix=='.xlsx':
        with zipfile.ZipFile(path) as z:return '\n'.join(z.read(n).decode('utf8') for n in z.namelist() if n.endswith(('.xml','.rels')))
    if path.suffix=='.gz':
        with gzip.open(path,'rt') as f:return f.read()
    if path.suffix in {'.csv','.json','.md','.svg'}:return path.read_text()
    return ''
def run(write=False):
    paths=sorted(p for area in AREAS for p in (ROOT/area).rglob('*') if p.is_file())
    registry=ROOT/'config/private/powerwatch_registry.json';identifiers=[]
    if registry.exists():
        for sensor in json.loads(registry.read_text())['sensors']:
            identifiers.append(sensor['source_sensor_serial'])
    failures=[]
    for p in paths:
        text=texts(p)
        if re.search(r'X-Amz-(?:Signature|Credential)|[?&](?:access_token|api_key|token)=',text,re.I):failures.append(str(p.relative_to(ROOT))+': signed URL/credential')
        if any(re.search(r'(?<![0-9a-z])'+re.escape(x)+r'(?![0-9a-z])',text,re.I) for x in identifiers):failures.append(str(p.relative_to(ROOT))+': controlled sensor identity')
        if p.name=='readings.csv.gz':
            with gzip.open(p,'rt') as f:header=next(csv.reader(f))
            if any(x in header for x in ['core_id','source_sensor_serial','facility_name','respondent_name','phone','latitude','longitude']):failures.append(str(p.relative_to(ROOT))+': private reading fields')
    snapshot=ROOT/'data/collections/ndosho/historical/charlie_kwh_snapshot_deidentified.xlsx'
    audit=json.loads(snapshot.with_name('preservation_audit.json').read_text())
    if digest(snapshot)!=audit['released_sha256']:failures.append('Workbook snapshot hash mismatch')
    manifest=json.loads(snapshot.with_name('source_manifest.json').read_text())
    if digest(snapshot)!=manifest['snapshot_sha256']:failures.append('Workbook source-manifest hash mismatch')
    inventory={'files':{str(p.relative_to(ROOT)):digest(p) for p in paths},
      'scope':'newly released packages and derived outputs; controlled originals excluded',
      'privacy_scan':'source sensor aliases checked when controlled registry present; no direct respondent text released'}
    if failures:raise ValueError('; '.join(failures))
    if write:INVENTORY.write_text(json.dumps(inventory,indent=2)+'\n')
    else:
        expected=json.loads(INVENTORY.read_text())
        if inventory['files']!=expected['files']:raise ValueError('Release inventory hashes differ; audit intentional changes before updating')
    return len(paths)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write-inventory',action='store_true');a=p.parse_args()
    print(f'Release checks passed: {run(a.write_inventory)} artifact hashes and privacy scans.')
