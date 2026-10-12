"""Verify controlled inputs before running the frozen production recipe."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
MANIFEST=json.loads(Path(__file__).with_name('input_manifest.json').read_text())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check-only',action='store_true');args=parser.parse_args()
    controlled=ROOT/'data/private/five_slide_v6'
    failures=[]
    for row in MANIFEST['inputs']:
        path=controlled/row['path']
        if not path.is_file():failures.append('missing: '+row['path'])
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:failures.append('checksum mismatch: '+row['path'])
    if failures:raise SystemExit('Controlled input preflight failed:\n'+'\n'.join(failures))
    if args.check_only:print('All controlled input checksums match.');return
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(controlled/'mpl-cache'))
    subprocess.run([sys.executable,str(controlled/'workspace/build_latest_five_slide_revision.py')],cwd=controlled/'workspace',env=env,check=True)
    from pypdf import PdfReader
    output=controlled/'workspace/final_five_slide_revision_20261012/oxygen_electricity_five_slide_review.pdf'
    assert len(PdfReader(output).pages)==5
    print('Built five slides:',output)
if __name__=='__main__':main()
