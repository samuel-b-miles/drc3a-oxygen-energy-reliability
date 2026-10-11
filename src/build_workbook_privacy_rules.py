#!/usr/bin/env python3
"""Rebuild controlled privacy rules for the inspected Charlie workbook snapshot.

Not a general-purpose anonymizer. Newly changed source text needs a new review.
Researchers' professional credits remain in the public source manifest; personal
annotations use role labels. The facility-label crosswalk stays ignored.
"""
import argparse,json,re,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def build(source:Path,output:Path):
    with zipfile.ZipFile(source) as z:
        texts=[''.join(s.itertext()) for s in ET.fromstring(z.read('xl/sharedStrings.xml'))]
    labels=sorted(set(t for t in texts if re.match(r'^(?:ch |hgr |csr |cs |cm |cclk$|hopital |sam home)',t,re.I)))
    replacements={label:('N001' if 'ndosho' in label.lower() else f'F{i:03d}') for i,label in enumerate(labels,1)}
    replacements.update({'CH CBCA Ndosho':'N001','Ndosho':'N001','Charlie Zujia Huang':'[source analyst]',
        'Charlie Huang':'[source analyst]','Aashika Nair':'[source annotator]','Allison Wong':'[source annotator]',
        'Samuel Miles':'[source collector]','Layla Kwong':'[source supervisor]','-Sam':'[source collector]',"Charlie's":'Analyst'})
    rules={'text_replacements':replacements,'tab_renames':{'saidi_ndosho':'saidi_N001'},
           'retained_professional_credit_strings':["Data Analysis by Charlie Huang, UC Berkeley EECS '28"],
           'forbidden_release_strings':labels+['Aashika Nair','Allison Wong','Samuel Miles','sam home','Charlie Zujia Huang']}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(rules,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=Path('data/raw/private/ndosho/historical/source.xlsx'))
    p.add_argument('--output',type=Path,default=Path('config/private/workbook_redactions.json'))
    a=p.parse_args();build(a.source,a.output)
