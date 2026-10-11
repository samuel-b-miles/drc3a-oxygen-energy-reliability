#!/usr/bin/env python3
"""Reproduce legacy mentions and audit narrower device categories from raw answers.

Raw answers, evidence spans, respondent/facility links and review queues stay in
ignored local files. Public outputs contain only whole-sample category counts.
The deterministic coding is a baseline for expert review, not a trained model.
"""
from __future__ import annotations
import argparse, ast, hashlib, json, platform, re, unicodedata
from pathlib import Path
import pandas as pd
from build_drc2_facility_master import add_standard_fields, make_respondent_sample

ROOT=Path(__file__).resolve().parents[1]
LEGACY=ROOT/'src/analyze_equipment_failure_frequency.py'
CONCENTRATOR_PATTERNS=[r'\bconcentr\w*',r'\bconcentret\w*',r'\bconscent\w*',r'\bcontracteur\s+d.?ox\w*']
OXYGEN_UNSPECIFIED=[r'\boxygen\w*']
NEGATION=re.compile(r'\b(?:aucun|aucune|pas de|sans|non)\s+(?:\w+\s+){0,2}$')
NO_DAMAGE=re.compile(r'^(?:rien|aucun(?:e)?|neant|ras|non|0|pas de probleme|pas de panne)[.! ]*$')

def normalize(value: object) -> str:
    if pd.isna(value): return ''
    s=unicodedata.normalize('NFKD',str(value).lower().strip())
    return ''.join(x for x in s if not unicodedata.combining(x)).replace('’',"'").replace('`',"'")

def legacy_patterns() -> dict:
    tree=ast.parse(LEGACY.read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CATEGORY_PATTERNS' for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('Legacy codebook not found')

def matches(text: str, patterns: list[str]) -> list[dict]:
    found=[]
    for pattern in patterns:
        for m in re.finditer(pattern,text,re.I):
            found.append({'pattern':pattern,'start_normalized':m.start(),'end_normalized':m.end(),
                          'matched_normalized':m.group(),'local_negation_candidate':bool(NEGATION.search(text[max(0,m.start()-55):m.start()]))})
    return found

def audited_patterns() -> dict:
    p=legacy_patterns().copy();p.pop('Oxygen concentrator / oxygen device')
    # Preserve comparator categories initially. Expert review must resolve their
    # broad roots too; narrowing oxygen alone is not sufficient validation.
    return {'Oxygen concentrator':CONCENTRATOR_PATTERNS,
            'Oxygen device unspecified':OXYGEN_UNSPECIFIED, **p}

def build(raw: Path, public: Path, private: Path) -> dict:
    public.mkdir(parents=True,exist_ok=True);private.mkdir(parents=True,exist_ok=True)
    df=add_standard_fields(pd.read_csv(raw))
    sample=make_respondent_sample(df)
    # Source data lineage uses original CSV line numbers; no text is released.
    facility_keys=sorted(df['A8_FOSA_num'].dropna().unique())
    fosa={v:f'F{i:04d}' for i,v in enumerate(facility_keys,1)}
    records=[];span_records=[];old=legacy_patterns();new=audited_patterns()
    for _,row in sample.iterrows():
        text=normalize(row['H1_a_medequip']);damage=pd.to_numeric(row['H1_medequip'],errors='coerce')
        item={'answer_id':f"A{int(row['raw_row_id']):04d}",'facility_id':fosa.get(row['A8_FOSA_num']),
              'source_csv_line':int(row['raw_row_id'])+1,'source_field':'H1_a_medequip',
              'answer_source':None if pd.isna(row['H1_a_medequip']) else str(row['H1_a_medequip']),
              'answer_normalized':text,'damage_response_code':None if pd.isna(damage) else int(damage),
              'reported_damage':bool(damage==1),'text_present':bool(text),'explicit_no_damage_text':bool(NO_DAMAGE.fullmatch(text)),
              'labels_status':'machine_rules_provisional_not_human_adjudicated'}
        for category,patterns in old.items(): item['legacy:'+category]=bool(matches(text,patterns))
        strict_found=matches(text,CONCENTRATOR_PATTERNS)
        for category,patterns in new.items():
            evidence=matches(text,patterns)
            # Unspecified oxygen is recorded only when no concentrator is named.
            if category=='Oxygen device unspecified' and strict_found: evidence=[]
            item[category]=bool(evidence)
            for ev in evidence:
                span_records.append({'answer_id':item['answer_id'],'facility_id':item['facility_id'],
                                     'source_csv_line':item['source_csv_line'],'source_field':'H1_a_medequip',
                                     'category':category,**ev})
        item['any_negation_candidate']=any(x['local_negation_candidate'] for x in span_records if x['answer_id']==item['answer_id'])
        item['yes_no_text_conflict']=bool(text and (damage!=1 or item['explicit_no_damage_text']))
        item['any_device_category']=any(item[c] for c in new)
        item['needs_review']=bool(text) # all non-empty answers, including negatives and uncoded text
        records.append(item)
    answers=pd.DataFrame(records)
    answers.to_csv(private/'answer_coding_ledger.csv',index=False)
    pd.DataFrame(span_records).to_csv(private/'matched_evidence_spans.csv',index=False)
    source_link=df[['raw_row_id','A8_FOSA_num','phone_clean','completeness_score']].copy()
    source_link['retained_by_legacy_rule']=source_link.raw_row_id.isin(sample.raw_row_id)
    source_link['facility_id']=source_link.A8_FOSA_num.map(fosa)
    retained=sample[['phone_clean','A8_FOSA_num','raw_row_id']].rename(columns={'raw_row_id':'retained_raw_row_id'})
    source_link=source_link.merge(retained,on=['phone_clean','A8_FOSA_num'],how='left',validate='many_to_one')
    source_link['source_csv_line']=source_link.raw_row_id+1
    source_link['retained_source_csv_line']=source_link.retained_raw_row_id+1
    source_link['selection_reason']=source_link.retained_by_legacy_rule.map({True:'retained_first_after_completeness_sort',False:'duplicate_phone_facility_pair'})
    source_link['source_sha256']=hashlib.sha256(raw.read_bytes()).hexdigest()
    source_link.to_csv(private/'source_to_respondent_crosswalk.csv',index=False)
    review=answers[answers.text_present].copy()
    review['human_reviewed']=False;review['reviewer_id']='';review['reviewed_labels_json']='';review['review_notes']=''
    # Re-running the audit must never overwrite completed human adjudication.
    if not (private/'human_review_queue.csv').exists(): review.to_csv(private/'human_review_queue.csv',index=False)
    facility=answers.groupby('facility_id',dropna=True).agg({
        'reported_damage':'max','text_present':'max','yes_no_text_conflict':'max',
        **{c:'max' for c in new},**{'legacy:'+c:'max' for c in old}})
    facility=facility.reindex(list(fosa.values()),fill_value=False)
    facility.to_csv(private/'coded_facility_mentions.csv')
    with_damage=facility[facility.reported_damage]
    with_text=facility[facility.text_present]
    freq=[]
    for c in new:
        count=int(facility[c].sum());damage_count=int(with_damage[c].sum());text_count=int(with_text[c].sum())
        freq.append({'category':c,'facilities_mentioning':count,'all_facilities_denominator':len(facility),
                     'percent_all_facilities':round(100*count/len(facility),3),
                     'facilities_mentioning_and_reporting_damage':damage_count,
                     'damage_reporting_facilities_denominator':len(with_damage),
                     'percent_damage_reporting_facilities':round(100*damage_count/len(with_damage),3) if len(with_damage) else None,
                     'text_answer_facilities_denominator':len(with_text),
                     'percent_text_answer_facilities':round(100*text_count/len(with_text),3) if len(with_text) else None,
                     'coding_status':'provisional_keyword_mentions_not_failure_incidence'})
    pd.DataFrame(freq).sort_values(['facilities_mentioning','category'],ascending=[False,True]).to_csv(public/'audited_device_mentions.csv',index=False)
    pd.DataFrame([{'category':c,'facilities_mentioning':int(facility['legacy:'+c].sum())} for c in old]).sort_values('facilities_mentioning',ascending=False).to_csv(public/'legacy_category_reproduction.csv',index=False)
    codebook=[{'category':c,'patterns':patterns,'rule':'any retained respondent per facility; multilabel; unspecified oxygen excluded when concentrator named'} for c,patterns in new.items()]
    (public/'codebook.json').write_text(json.dumps(codebook,ensure_ascii=False,indent=2)+'\n')
    summary={'source_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
         'legacy_script_sha256':hashlib.sha256(LEGACY.read_bytes()).hexdigest(),
         'raw_rows':len(df),'raw_columns':len(pd.read_csv(raw,nrows=0).columns),
         'retained_respondents_legacy_rule':len(sample),'facility_denominator':len(facility),
         'missing_facility_id_rows':int(df.A8_FOSA_num.isna().sum()),
         'missing_phone_rows':int(df.phone_clean.isna().sum()),
         'dropped_rows_legacy_rule':len(df)-len(sample),'damage_reporting_facilities':len(with_damage),
         'facilities_with_nonempty_equipment_text':len(with_text),'nonempty_answers_for_review':len(review),
         'answers_with_yes_no_text_conflict':int(answers.yes_no_text_conflict.sum()),
         'answers_with_negation_candidate':int(answers.any_negation_candidate.sum()),
         'nonempty_answers_without_device_category':int((answers.text_present & ~answers.any_device_category).sum()),
         'concentrator_facilities_all_mentions':int(facility['Oxygen concentrator'].sum()),
         'concentrator_facilities_reporting_damage':int(with_damage['Oxygen concentrator'].sum()),
         'claim_scope':'facilities mentioning a concentrator in self-reported equipment-damage context; not risk per installed device or independently confirmed causation',
         'method':'deterministic multilabel keyword coding; expert adjudication and supervised model evaluation pending',
         'python':platform.python_version(),'pandas':pd.__version__,
         'dedup_rule':'existing completeness sort then first normalized-phone + facility pair; missing-phone and tie cases require sensitivity review',
         'timestamp_scope':'submission timestamps, not verified interview dates',
         'submission_time_start':str(df.submission_time_parsed.min()),'submission_time_end':str(df.submission_time_parsed.max())}
    (public/'run_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=Path('data/raw/private/drc2/original_survey_export.csv'))
    p.add_argument('--public-out',type=Path,default=Path('outputs/drc2_failure_audit'))
    p.add_argument('--private-out',type=Path,default=Path('outputs/private/drc2_failure_audit'))
    a=p.parse_args();print(json.dumps(build(a.raw,a.public_out,a.private_out),indent=2))
