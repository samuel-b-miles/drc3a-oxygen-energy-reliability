#!/usr/bin/env python3
"""Retrieve pinned public source bytes into ignored local staging, checking SHA256."""
import argparse, hashlib, json, urllib.request
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,default=Path('data/collections/ndosho/hopmeter/source_manifest.json'))
    p.add_argument('--output',type=Path,default=Path('data/raw/private/ndosho/hopmeter/source_repo/data'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    for item in json.loads(a.manifest.read_text())['series']:
        dest=a.output/item['source_filename']
        if not dest.exists():
            temp=dest.with_suffix('.download');urllib.request.urlretrieve(item['download_url'],temp)
            if hashlib.sha256(temp.read_bytes()).hexdigest()!=item['source_sha256']:
                temp.unlink();raise ValueError('Downloaded source hash mismatch')
            temp.replace(dest)
        if hashlib.sha256(dest.read_bytes()).hexdigest()!=item['source_sha256']:
            raise ValueError('Local source hash mismatch: '+item['series_id'])
        print(item['series_id']+' verified')
