#!/usr/bin/env python3
"""Release only approved pseudonymous fields from controlled normalized exports."""
from pathlib import Path
import argparse, csv, gzip, hashlib, json, shutil
from audit_powerwatch_exports import FIELDS

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def release(normalized, manifest_path, registry_path, destination):
    normalized, destination = Path(normalized), Path(destination)
    manifest=json.loads(Path(manifest_path).read_text())
    registry=json.loads(Path(registry_path).read_text())
    destination.mkdir(parents=True,exist_ok=True)
    with (normalized/'readings.csv').open(newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames != FIELDS: raise ValueError('Unexpected public reading fields')
        sites={x['site_id'] for x in registry['sites']}; sensors={x['sensor_id'] for x in registry['sensors']}
        count=0
        for row in reader:
            if row['site_id'] not in sites or row['sensor_id'] not in sensors: raise ValueError('Unknown pseudonym')
            count+=1
    # Deterministic compression, no source path or timestamp in gzip header.
    with (destination/'readings.csv.gz').open('wb') as target:
        with gzip.GzipFile(filename='',mode='wb',fileobj=target,mtime=0) as compressed:
            compressed.write((normalized/'readings.csv').read_bytes())
    for name in ['coverage.csv','selected_site_returns.csv','run_provenance.json']:
        shutil.copyfile(normalized/name,destination/name)
    allowed_export={'export_id','sha256','bytes','acquired_at_utc','source_url','organization_id','panel_title',
      'query_start_local','query_end_exclusive_local','source_timezone','timestamp_format','selected_site_ids',
      'include_outages','formatted_data','download_for_excel','aggregation_status','active_for_pipeline',
      'actual_ui_query_end_local','denominator_note'}
    released={k:manifest[k] for k in ['schema_version','source_provider','status','query_evidence'] if k in manifest}
    released['exports']=[{k:v for k,v in x.items() if k in allowed_export} for x in manifest['exports']]
    released['released_readings_sha256']=digest(destination/'readings.csv.gz')
    released['release_pipeline_sha256']=digest(Path(__file__))
    (destination/'export_manifest.json').write_text(json.dumps(released,indent=2)+'\n')
    allowed_site={'site_id','collection_id','case_label','requested_for_goma_export'}
    allowed_sensor={'site_id','sensor_id','circuit_id','mapping_status','valid_from','valid_to'}
    public={'sites':[{k:v for k,v in x.items() if k in allowed_site} for x in registry['sites']],
            'sensors':[{k:v for k,v in x.items() if k in allowed_sensor} for x in registry['sensors']],
            'status':'pseudonymous; physical sensor identities and dated circuit crosswalk controlled'}
    # Replace private source labels; two explicitly named study cases are approved.
    for site in public['sites']:
        site['case_label']={'S004':'Ndosho','S010':'Kyeshero (unreconciled)'}.get(site['site_id'],site['site_id'])
    (destination/'series_registry.json').write_text(json.dumps(public,indent=2)+'\n')
    return {'released_rows':count,'sha256':released['released_readings_sha256']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for x in ['normalized','manifest','registry','destination']:p.add_argument('--'+x,type=Path,required=True)
    a=p.parse_args(); print(json.dumps(release(a.normalized,a.manifest,a.registry,a.destination)))
