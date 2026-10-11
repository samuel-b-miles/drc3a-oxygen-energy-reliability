#!/usr/bin/env python3
"""Optional supervised multilabel baseline after independent answer adjudication.

Requires every non-empty answer in the queue to have reviewed labels. Prevents
training on machine suggestions as if they were independently verified labels.
All inputs, predictions and models must be written below ignored outputs/private.
"""
from __future__ import annotations
import argparse,hashlib,json,pickle
from pathlib import Path
import pandas as pd

def load_reviewed(path: Path, categories: list[str]) -> tuple[pd.DataFrame,pd.DataFrame]:
    df=pd.read_csv(path,keep_default_na=False)
    if df.empty or not df['human_reviewed'].astype(str).str.lower().eq('true').all():
        raise ValueError('Independent adjudication is incomplete; refusing to train on provisional rule labels')
    if df['reviewer_id'].str.strip().eq('').any(): raise ValueError('Every reviewed answer needs a reviewer identifier')
    rows=[]
    for value in df.reviewed_labels_json:
        labels=json.loads(value)
        if not isinstance(labels,list) or any(x not in categories for x in labels): raise ValueError('Invalid adjudicated label set')
        rows.append({c:int(c in labels) for c in categories})
    if df.answer_id.duplicated().any(): raise ValueError('Duplicate answer identifier')
    return df,pd.DataFrame(rows)

def build(review: Path, codebook: Path, output: Path):
    categories=[x['category'] for x in json.loads(codebook.read_text())]
    df,y=load_reviewed(review,categories)
    if 'outputs/private' not in output.as_posix(): raise ValueError('Model artifacts must remain controlled')
    from sklearn import __version__ as sklearn_version
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import GroupKFold,cross_val_predict
    from sklearn.metrics import precision_recall_fscore_support
    output.mkdir(parents=True,exist_ok=True)
    metrics=[];prediction=df[['answer_id','facility_id']].copy()
    for c in categories:
        positives=df.loc[y[c].eq(1),'facility_id'].nunique();negatives=df.loc[y[c].eq(0),'facility_id'].nunique()
        if min(positives,negatives)<10:
            metrics.append({'category':c,'status':'deferred_insufficient_independently_labeled_facilities','positive_facilities':positives});continue
        model=Pipeline([('text',TfidfVectorizer(analyzer='char',ngram_range=(3,5),min_df=2)),
                       ('classifier',LogisticRegression(C=1,class_weight='balanced',max_iter=2000,random_state=20261011))])
        splitter=GroupKFold(n_splits=5)
        splits=list(splitter.split(df.answer_normalized,y[c],groups=df.facility_id))
        if any(y[c].iloc[train].nunique()<2 for train,test in splits):
            metrics.append({'category':c,'status':'deferred_single_class_training_fold'});continue
        scores=cross_val_predict(model,df.answer_normalized,y[c],cv=splits,method='predict_proba')[:,1]
        predicted=(scores>=0.5).astype(int)
        p,r,f,_=precision_recall_fscore_support(y[c],predicted,average='binary',zero_division=0)
        metrics.append({'category':c,'status':'evaluated_grouped_5_fold','precision':float(p),'recall':float(r),'f1':float(f),'positive_facilities':positives})
        prediction[c+':out_of_fold_probability']=scores
        model.fit(df.answer_normalized,y[c])
        with (output/(c.lower().replace('/','_').replace(' ','_')+'.pkl')).open('wb') as stream:pickle.dump(model,stream)
    prediction.to_csv(output/'out_of_fold_predictions.csv',index=False)
    card={'method':'character 3–5 gram TF-IDF and balanced logistic regression per label','threshold':0.5,
          'validation':'five folds grouped by facility; vocabulary learned inside each training fold',
          'limitations':'internal validation only; prediction uncertainty is not uncertainty in actual device failure rates',
          'training_source_sha256':hashlib.sha256(review.read_bytes()).hexdigest(),'sklearn_version':sklearn_version,'metrics':metrics}
    (output/'model_card.json').write_text(json.dumps(card,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--review',type=Path,default=Path('outputs/private/drc2_failure_audit/human_review_queue.csv'))
    p.add_argument('--codebook',type=Path,default=Path('outputs/drc2_failure_audit/codebook.json'))
    p.add_argument('--output',type=Path,default=Path('outputs/private/drc2_equipment_model'))
    a=p.parse_args();build(a.review,a.codebook,a.output)
