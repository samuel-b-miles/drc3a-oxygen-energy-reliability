#!/usr/bin/env python3
"""Lossless text projection of released XLSX cells with cached values and formulas."""
import argparse,csv,gzip,json,posixpath,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from preserve_source_workbook import NS

def build(source: Path, output: Path):
    with zipfile.ZipFile(source) as z:
        strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
        rels={e.attrib['Id']:posixpath.normpath('xl/'+e.attrib['Target']) for e in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        fieldnames=['sheet','cell','type','literal_or_cached_value','formula','style_id']
        inventory=[]
        with output.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
            import io
            with io.TextIOWrapper(gz,encoding='utf-8',newline='') as text:
                w=csv.DictWriter(text,fieldnames=fieldnames);w.writeheader()
                for sheet in ET.fromstring(z.read('xl/workbook.xml')).find(NS+'sheets'):
                    path=rels[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
                    count=formulas=errors=0
                    for c in ET.fromstring(z.read(path)).iter(NS+'c'):
                        v=c.find(NS+'v'); f=c.find(NS+'f'); t=c.attrib.get('t','n')
                        value=v.text if v is not None else ''
                        if t=='s' and value is not None: value=strings[int(value)]
                        if t=='inlineStr': value=''.join(c.find(NS+'is').itertext())
                        if value in ('',None) and f is None: continue
                        w.writerow({'sheet':sheet.attrib['name'],'cell':c.attrib['r'],'type':t,
                                    'literal_or_cached_value':value,'formula':('='+f.text) if f is not None and f.text else '',
                                    'style_id':c.attrib.get('s','')})
                        count+=1;formulas+=int(f is not None);errors+=int(t=='e')
                    inventory.append({'sheet':sheet.attrib['name'],'nonempty_cells':count,'formula_cells':formulas,'existing_error_cells':errors})
    output.with_name('sheet_inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps({'worksheets':len(inventory),'exported_cells':sum(x['nonempty_cells'] for x in inventory)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();build(a.source,a.output)
