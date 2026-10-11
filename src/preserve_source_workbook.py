#!/usr/bin/env python3
"""De-identify an XLSX without recalculating or reserializing worksheet cells.

Use this for a source snapshot, not a corrected analytical workbook. Numeric,
date, formula, error and cached-value XML are compared before and after. Text
replacement rules and original identity crosswalks are controlled inputs.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
EMAIL = re.compile(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', re.I)
URL = re.compile(r'https?://[^\s<>]+')

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def cell_signature(z: zipfile.ZipFile, tab_renames: dict | None = None) -> tuple[str, dict]:
    rows, counts = [], {'formula_cells': 0, 'existing_error_cells': 0, 'non_text_cells': 0}
    for name in z.namelist():
        if not re.fullmatch(r'xl/worksheets/sheet\d+\.xml', name):
            continue
        for c in ET.fromstring(z.read(name)).iter(NS+'c'):
            if c.attrib.get('t') in {'s','inlineStr','str'} and c.find(NS+'f') is None:
                continue
            record = [name, sorted(c.attrib.items()), [[x.tag, sorted(x.attrib.items()), x.text] for x in c]]
            for child in record[2]:
                if child[0] == NS+'f' and child[2]:
                    for old,new in (tab_renames or {}).items(): child[2] = child[2].replace(old,new)
            rows.append(record)
            counts['non_text_cells'] += 1
            counts['formula_cells'] += int(c.find(NS+'f') is not None)
            counts['existing_error_cells'] += int(c.attrib.get('t') == 'e')
    return digest(json.dumps(rows, ensure_ascii=False, separators=(',',':')).encode()), counts

def build(source: Path, rules_path: Path, dest: Path, audit_dir: Path) -> dict:
    rules = json.loads(rules_path.read_text())
    replacements = sorted(rules['text_replacements'].items(), key=lambda x: -len(x[0]))
    changes = []
    def scrub(s: str, location: str) -> str:
        old = s
        if s in rules.get('retained_professional_credit_strings',[]):
            return s
        for needle, replacement in replacements:
            s = re.sub(re.escape(needle), lambda _: replacement, s, flags=re.I)
        s = EMAIL.sub('[contact redacted]', s)
        s = URL.sub('[external link omitted; see source manifest]', s)
        if s != old:
            changes.append({'part': location, 'action':'text_deidentified', 'original_text_sha256':digest(old.encode()), 'released_text':s})
        return s
    dest.parent.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as src, zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED) as out:
        before, counts = cell_signature(src, rules.get('tab_renames',{}))
        for info in src.infolist():
            name, data = info.filename, src.read(info.filename)
            if name.startswith('xl/media/'):
                changes.append({'part':name,'action':'embedded_poster_omitted','original_text_sha256':digest(data),'released_text':''})
                continue
            if name.endswith('.xml') or name.endswith('.rels'):
                text = data.decode('utf-8')
                for old,new in rules.get('tab_renames',{}).items(): text=text.replace(old,new)
                if name == 'xl/sharedStrings.xml' or re.fullmatch(r'xl/worksheets/sheet\d+\.xml',name):
                    # Only literal text elements; formula/cached numeric nodes remain byte-identical.
                    text = re.sub(r'(<(?:\w+:)?t(?:\s[^>]*)?>)(.*?)(</(?:\w+:)?t>)',
                                  lambda m: m[1]+scrub(m[2],name)+m[3],text,flags=re.S)
                    # Private Google Slides links are removed, not replaced by broken hyperlink targets.
                    text = re.sub(r'<hyperlinks>.*?</hyperlinks>', '', text, flags=re.S)
                    if name == 'xl/worksheets/sheet1.xml':
                        text = re.sub(r'<drawing\b[^>]*/>', '', text)
                elif 'comment' in name.lower():
                    text = re.sub(r'(<(?:\w+:)?t(?:\s[^>]*)?>)(.*?)(</(?:\w+:)?t>)',
                                  lambda m: m[1]+scrub(m[2],name)+m[3],text,flags=re.S)
                    text = re.sub(r'<author>.*?</author>','<author>Source annotation</author>',text,flags=re.S)
                elif name.startswith('docProps/'):
                    for tag in ['dc:creator','cp:lastModifiedBy']:
                        text = re.sub(fr'<{tag}>.*?</{tag}>',fr'<{tag}>DRC3a source package</{tag}>',text,flags=re.S)
                elif name.endswith('.rels'):
                    text = re.sub(r'<Relationship\b[^>]*TargetMode="External"[^>]*/>', '', text)
                    if name == 'xl/worksheets/_rels/sheet1.xml.rels':
                        text = re.sub(r'<Relationship\b[^>]*Type="[^"]*/drawing"[^>]*/>', '', text)
                elif name == '[Content_Types].xml':
                    text = re.sub(r'<Override\b[^>]*PartName="/xl/drawings/drawing1.xml"[^>]*/>', '', text)
                elif name.startswith('xl/charts/'):
                    text = re.sub(r'(<(?:\w+:)?(?:t|v)(?:\s[^>]*)?>)(.*?)(</(?:\w+:)?(?:t|v)>)',
                                  lambda m: m[1]+scrub(m[2],name)+m[3],text,flags=re.S)
                # Retain original tab names and references, including provider name Virunga.
                data = text.encode('utf-8')
            if name in {'xl/drawings/drawing1.xml','xl/drawings/_rels/drawing1.xml.rels'}:
                changes.append({'part':name,'action':'poster_drawing_omitted','original_text_sha256':digest(data),'released_text':''})
                continue
            out.writestr(info, data)
    with zipfile.ZipFile(dest) as released:
        after, released_counts = cell_signature(released)
        if before != after or counts != released_counts:
            raise ValueError('Source numeric/date/formula/cache/error cells changed')
        bad = []
        for name in released.namelist():
            if name.endswith('.xml') or name.endswith('.rels'):
                text = released.read(name).decode('utf-8')
                if EMAIL.search(text): bad.append(name+': email')
                for needle in rules['forbidden_release_strings']:
                    if needle.casefold() in text.casefold(): bad.append(name+': forbidden identity')
        if bad: raise ValueError('Privacy scan failed: '+', '.join(sorted(set(bad))))
        sheets = ET.fromstring(released.read('xl/workbook.xml')).find(NS+'sheets')
        sheet_names = [s.attrib['name'] for s in sheets]
    with (audit_dir/'redaction_ledger.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['part','action','original_text_sha256','released_text']);w.writeheader();w.writerows(changes)
    result = {'source_sha256':digest(source.read_bytes()), 'released_sha256':digest(dest.read_bytes()),
              'snapshot_policy':'no_recalculation_existing_source_errors_retained',
              'preserved_cell_signature_sha256':before, **counts, 'worksheets':sheet_names,
              'privacy_changes':len(changes),'privacy_scan':'passed',
              'anonymity_scope':'deidentified workbook; named case and source citation prevent a claim of irreversible anonymity'}
    (audit_dir/'preservation_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--rules',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--audit-dir',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.source,a.rules,a.output,a.audit_dir),indent=2))
