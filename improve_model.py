"""Reproducible v2: validation-only selection, disjoint original-row holdout."""
import argparse,csv,io,json,zipfile,time,os
from pathlib import Path
import joblib,numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from engine import normalize,History,metric_report,select_threshold

def archive_signature(path):
    with zipfile.ZipFile(path) as z:
        return [(i.filename,i.CRC,i.file_size) for i in z.infolist() if i.filename.lower().endswith('.csv')]

def prepare(archive,cache):
    parts=[[],[],[]];total=0;fraud=0
    with zipfile.ZipFile(archive) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(names)!=1:raise ValueError('Expected exactly one CSV.')
        with z.open(names[0]) as file:
            for i,r in enumerate(csv.DictReader(io.TextIOWrapper(file,encoding='utf-8-sig'))):
                step=int(r['step']);label=int(r['isFraud']);total+=1;fraud+=label
                p=0 if step<400 else 1 if step<555 else 2
                # Enrich training only. Validation/test selection is label independent.
                keep=(label==1 or i%24==0) if p==0 else i%8==1
                if keep:
                    r['id']=f'PS-{i+1:07d}';parts[p].append(normalize(r,i))
    data=dict(parts=parts,total=total,fraud=fraud,archive_signature=archive_signature(archive))
    joblib.dump(data,cache)
    return data

def run(archive,runtime):
    runtime.mkdir(parents=True,exist_ok=True);cache=runtime/'v2-training-cache.joblib'
    data=joblib.load(cache) if cache.exists() else None
    if data is None or data.get('archive_signature')!=archive_signature(archive):data=prepare(archive,cache)
    parts=data['parts'];h=History();xs=[];ys=[]
    for part in parts:
        features=[]
        for r in part:
            x,_=h.features(r);features.append(x);h.add(r)
        xs.append(np.asarray(features,dtype=np.float32));ys.append(np.asarray([r['isFraud'] for r in part]))
    print('Partitions:',[(len(y),int(y.sum())) for y in ys],flush=True)
    # This list and policy are fixed before evaluating the final holdout.
    candidates=[('Time-aware balanced',list(range(6))+[10,11,12],'balanced'),('Account-context balanced',list(range(17)),'balanced'),('Account-context moderate',list(range(17)),{0:1,1:20})]
    results=[]
    for name,indices,weight in candidates:
        model=HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,max_depth=6,min_samples_leaf=30,l2_regularization=5,learning_rate=.08,class_weight=weight,early_stopping=False,random_state=2026)
        model.fit(xs[0][:,indices],ys[0]);prob=model.predict_proba(xs[1][:,indices])[:,1]
        threshold=select_threshold(ys[1],prob,budget=.005);report=metric_report(ys[1],prob,threshold)
        # Fixed priority: validation recall under false-positive budget, then precision.
        results.append(dict(name=name,indices=indices,model=model,threshold=threshold,validation=report))
        print('Validation:',name,json.dumps(report),flush=True)
    best=max(results,key=lambda r:(r['validation']['recall'],r['validation']['precision']))
    # First and only look at final test predictions after model/policy selection.
    newprob=best['model'].predict_proba(xs[2][:,best['indices']])[:,1]
    oldpath=runtime/'v1-model.joblib'
    if not oldpath.exists():
        current=runtime/'model.joblib'
        if current.exists() and joblib.load(current).get('version')=='history-hgb-v1':
            old=joblib.load(current)
        else:
            # Fresh LinuxONE setup has no Windows baseline artifact. Fit a
            # clearly labelled unweighted reference using training data only.
            reference=HistGradientBoostingClassifier(max_iter=75,max_leaf_nodes=15,l2_regularization=2,random_state=7)
            reference.fit(xs[0][:,:10],ys[0])
            old=dict(model=reference,threshold=select_threshold(ys[1],reference.predict_proba(xs[1][:,:10])[:,1]),version='native-reference')
        joblib.dump(old,oldpath)
    old=joblib.load(oldpath)
    oldprob=old['model'].predict_proba(xs[2][:,:10])[:,1]
    baseline_name='Unweighted native reference' if old.get('version')=='native-reference' else 'Original v1 (same new holdout)'
    reports={baseline_name:metric_report(ys[2],oldprob,old['threshold']),'Improved v2':metric_report(ys[2],newprob,best['threshold'])}
    protocol=dict(policy='Maximise validation recall at <=0.5% legitimate-payment false-positive rate; select candidate on validation recall then precision.',training='step < 400; all fraud and every 24th original legitimate row',validation='400 <= step < 555; original row index modulo 8 equals 1',test='step >= 555; original row index modulo 8 equals 1; excludes every-64th-row original test',history='Observed retained rows only, in file order within each hour; incomplete account history.',limitations='Synthetic dataset, temporal distribution shift, simulation-hour feature may exploit simulator regularity; no real-bank generalisation claim. The old v1 used a different training window. Precision/recall changes are model-and-policy changes, not a controlled single-feature ablation.',candidate=best['name'],validation_report=best['validation'])
    bundle=dict(model=best['model'],feature_indices=best['indices'],source='PaySim · improved v2 · unseen-row evaluation',reports=reports,threshold=best['threshold'],test_rows=parts[2],seed_rows=parts[0]+parts[1],split=dict(train=len(parts[0]),validation=len(parts[1]),test=len(parts[2])),version='paysim-hgb-v2',protocol=protocol)
    manifest=dict(full_rows=data['total'],full_fraud=data['fraud'],split=bundle['split'],protocol=protocol,validation_candidates=[dict(name=r['name'],validation=r['validation']) for r in results],reports=reports)
    temporary=runtime/'next-model.joblib';joblib.dump(bundle,temporary);os.replace(temporary,runtime/'model.joblib')
    (runtime/'paysim-evaluation.json').write_text(json.dumps(manifest,indent=2))
    print('FINAL',json.dumps(manifest,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('--runtime',default=str(Path(__file__).parent/'runtime'));args=parser.parse_args()
    run(args.archive,Path(args.runtime))

