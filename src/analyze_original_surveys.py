"""Conservative, auditable original FOSA/MCZ analysis. Never publishes row-level data."""
import argparse, csv, hashlib, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

def norm(v):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(v or '')).casefold()).strip()

def coding_text(v):
    return ''.join(c for c in unicodedata.normalize('NFKD',norm(v)) if not unicodedata.combining(c))

def fingerprint(row):
    # Exact cells, not semantic similarity. Preserve distinct responses and punctuation.
    row = list(row)
    while row and row[-1] in ('', None): row.pop()
    return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def deduplicate(rows):
    seen, kept, audit = {}, [], []
    for source_row, row in rows:
        fp=fingerprint(row)
        if fp in seen: audit.append({'source_row':source_row,'retained_source_row':seen[fp],'rule':'exact_cells_except_trailing_empty'})
        else: seen[fp]=source_row; kept.append((source_row,row))
    return kept,audit

# These broad categories are exploratory dictionary flags, not human-validated codes.
PATTERNS={
 'concentrator_explicit':r'concentrat|extra[ci]teur.{0,8}oxyg',
 'resuscitation_broad':r'resusc|reanim',
 'sterilization':r'steril|autoclav',
 'refrigeration_cold_chain':r'refrig|frigo|cold|blood storage|vaccin',
 'imaging':r'x.ray|radiogra|echogra|ultrasound|echograph',
 'laboratory':r'laborat|microsc|centrifug|hemat|haemat',
 'surgery':r'surger|chirurg|operation',
 'maternal_neonatal':r'matern|neonat|accouch|incubat|couveuse',
}
FIELDS={
 'FOSA_MED':{17:'all_cause_equipment_failure',18:'power_attributed_equipment_failure'},
 'FOSA_TECH':{7:'rank_peak_power_load',8:'rank_energy_consumption',9:'rank_equipment_failure',10:'rank_mortality_importance'},
 'Responses':{14:'mortality_relevant_power_impacts',16:'health_challenge',17:'power_attributed_equipment_failure',20:'power_attributed_equipment_failure',22:'mortality_relevant_power_impacts'}
}

def screen_codes(tab, context, text):
    codes=[c for c,p in PATTERNS.items() if re.search(p,coding_text(text))]
    if tab=='FOSA_TECH' and context in ('rank_peak_power_load','rank_energy_consumption') and 'resuscitation_broad' in codes:
        codes=[c for c in codes if c!='concentrator_explicit']
    return codes

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def run(root):
    private=root/'data/private/original_surveys';out=root/'outputs/tables/original_surveys';out.mkdir(parents=True,exist_ok=True)
    corpus={k:json.loads((private/(k+'.json')).read_text()) for k in ('fosa','mcz')}
    records=[];audits=[];summary=[];counts=[];lineage=[]
    for source,tab in [('fosa','FOSA_MED'),('fosa','FOSA_TECH'),('mcz','Responses')]:
        values=corpus[source]['sheets'][tab]['values']; rows=[(i,r) for i,r in enumerate(values[1:],2) if r and r[0] not in ('',None)]
        kept,dups=deduplicate(rows)
        for d in dups:audits.append(dict(tab=tab,**d))
        summary.append({'corpus':tab,'nonempty_rows':len(rows),'exact_duplicate_copies':len(dups),'retained_submissions':len(kept),'missing_export_counter':sum(not norm(r[0]) for _,r in kept)})
        per_context=defaultdict(list)
        facility_context=defaultdict(lambda:defaultdict(set))
        status_context=defaultdict(Counter)
        valid_context=defaultdict(list)
        candidates=defaultdict(list)
        for rn,row in kept:
            rid=f'{tab}:{rn}'
            facility=norm(row[5] if tab!='Responses' else row[4])
            candidates[facility].append(rn)
            records.append({'record_id':rid,'source_row':rn,'tab':tab,'values_json':json.dumps(row,ensure_ascii=False)})
            lineage.append({'record_id':rid,'source_row':rn,'tab':tab,'sha256':fingerprint(row)})
            contexts=defaultdict(list)
            for idx,context in FIELDS[tab].items():
                if idx<len(row) and row[idx] not in ('',None):contexts[context].append(str(row[idx]))
            for context,texts in contexts.items():
                text=' | '.join(texts)
                # URL-only answers are not transcribed evidence.
                if re.fullmatch(r'https?://\S+',text.strip()):continue
                codes=screen_codes(tab,context,text)
                status='numeric_only_unmapped' if re.fullmatch(r'[\d\s,;.|]+',text) else 'text_not_adjudicated'
                status_context[context][status]+=1
                if norm(row[0]): valid_context[context].append(set(codes))
                per_context[context].append(set(codes))
                facility_context[context][facility].update(codes)
                for code in codes:
                    lineage.append({'record_id':rid,'source_row':rn,'tab':tab,'sha256':'','context':context,'code':code,'verbatim':text,'review_status':'dictionary_flag_unreviewed'})
        write_csv(private/(tab+'_same_label_review.csv'),[{'normalized_location':k,'source_rows':'|'.join(map(str,v)),'decision':'retain_pending_review'} for k,v in candidates.items() if len(v)>1],['normalized_location','source_rows','decision'])
        for context,code_sets in per_context.items():
            for code in PATTERNS:
                n=sum(code in s for s in code_sets)
                counts.append({'corpus':tab,'elicitation_context':context,'code':code,'n_mentions':n,'n_nonempty_answers':len(code_sets),'percent':round(100*n/len(code_sets),1),'unique_location_labels_mentioning':sum(code in v for v in facility_context[context].values()),'unique_location_labels_answered':len(facility_context[context]),'numeric_only_unmapped_answers':status_context[context]['numeric_only_unmapped'],'nonblank_counter_mentions':sum(code in c for c in valid_context[context]),'nonblank_counter_answered':len(valid_context[context])})
    write_csv(private/'cleaned_submissions.csv',records,['record_id','source_row','tab','values_json'])
    write_csv(private/'exact_duplicate_audit.csv',audits,['tab','source_row','retained_source_row','rule'])
    write_csv(private/'coding_and_lineage.csv',lineage,['record_id','source_row','tab','sha256','context','code','verbatim','review_status'])
    write_csv(out/'deduplication_summary.csv',summary,list(summary[0]))
    write_csv(out/'thematic_flags.csv',counts,list(counts[0]))
    # Copy tabs are provenance checks, never additional observations.
    primary=corpus['mcz']['sheets']['Responses']['values']; header=primary[0]
    by_session={str(r[3]):dict(zip(header,r)) for r in primary[1:] if len(r)>3 and r[3]}
    copy_audit=[]
    for tab in ['Copy of Responses','Sheet3']:
        vs=corpus['mcz']['sheets'][tab]['values']; hi=next(i for i,r in enumerate(vs) if 'session' in r)
        h=vs[hi]
        for rn,r in enumerate(vs[hi+1:],hi+2):
            d=dict(zip(h,r));session=str(d.get('session',''))
            if not session:continue
            base=by_session.get(session)
            differences=[] if base is None else [k for k in set(base)&set(d) if k and base[k]!=d[k]]
            copy_audit.append({'tab':tab,'source_row':rn,'session':session,'matched_primary':bool(base),'differing_fields':'|'.join(sorted(differences))})
    write_csv(private/'copy_tab_audit.csv',copy_audit,['tab','source_row','session','matched_primary','differing_fields'])
    copy_summary=[{'tab':tab,'rows':sum(r['tab']==tab for r in copy_audit),'matched_primary_sessions':sum(r['tab']==tab and r['matched_primary'] for r in copy_audit),'rows_with_differences':sum(r['tab']==tab and bool(r['differing_fields']) for r in copy_audit)} for tab in ['Copy of Responses','Sheet3']]
    write_csv(out/'copy_tab_summary.csv',copy_summary,list(copy_summary[0]))
    manifest={'extracted_date':'2026-11-12','source_files':{k+'.json':hashlib.sha256((private/(k+'.json')).read_bytes()).hexdigest() for k in corpus},'method':'exact-cell duplicate removal only; derived tabs excluded','codebook_version':'0.1-dictionary-pilot'}
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'deduplication':summary,'copies':copy_summary},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);run(p.parse_args().root)
