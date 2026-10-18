"""Past-only stream context; validation selection before a fresh final holdout."""
import os,argparse,json,csv,io,zipfile
from pathlib import Path
import numpy as np,joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from engine import StreamContext,History,normalize,metric_report,select_threshold
from train_v3 import policy
from improve_model import archive_signature

def prepare(archive,runtime):
    cache=runtime/'sequence-data.joblib';signature=archive_signature(archive)
    if cache.exists():
        data=joblib.load(cache)
        if data.get('signature')==signature:return data
    parts=[[],[],[]];stream=StreamContext()
    with zipfile.ZipFile(archive) as z:
        files=[n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(files)!=1:raise ValueError('Expected one CSV.')
        with z.open(files[0]) as f:
            for i,raw in enumerate(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig'))):
                row=normalize(raw,i);p=0 if row['step']<400 else 1 if row['step']<555 else 2
                keep=(row['isFraud']==1 or i%24==0) if p==0 else i%8==(1 if p==1 else 3)
                if keep:
                    row['id']=f'PS-{i+1:07d}';row['_stream_context']=stream.features(row);parts[p].append(row)
                stream.add(row)
    data=dict(parts=parts,signature=signature);joblib.dump(data,cache);return data

def run(archive,runtime):
    runtime.mkdir(parents=True,exist_ok=True)
    data=prepare(archive,runtime);parts=data['parts'];xs=[];ys=[];history=History()
    for part in parts:
        features=[]
        for r in part:
            x,_=history.features(r);features.append(x);history.add(r)
        xs.append(np.asarray(features,dtype=np.float32));ys.append(np.asarray([r['isFraud'] for r in part]))
    baseline_path=runtime/'v2-model.joblib'
    if baseline_path.exists():old=joblib.load(baseline_path)
    else:
        # Native first-time deployment can reproduce the V2-style reference
        # without importing a Windows artifact or opening the test labels.
        reference=HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,max_depth=6,min_samples_leaf=30,l2_regularization=5,learning_rate=.08,class_weight={0:1,1:20},early_stopping=False,random_state=2026)
        reference.fit(xs[0][:,:17],ys[0]);v=reference.predict_proba(xs[1][:,:17])[:,1]
        old=dict(model=reference,feature_indices=list(range(17)),threshold=select_threshold(ys[1],v),version='v2-native-reference')
        joblib.dump(old,baseline_path)
    previous_validation=metric_report(ys[1],old['model'].predict_proba(xs[1][:,old['feature_indices']])[:,1],old['threshold'])
    print('Partitions',[(len(y),int(y.sum())) for y in ys],flush=True)
    results=[]
    for name,weight in [('Sequence unweighted',None),('Sequence moderate',{0:1,1:3}),('Sequence cost-aware',{0:1,1:10})]:
        path=runtime/(name.lower().replace(' ','-')+'.joblib')
        if path.exists():model=joblib.load(path)
        else:
            model=HistGradientBoostingClassifier(max_iter=250,max_leaf_nodes=23,max_depth=7,min_samples_leaf=25,l2_regularization=3,learning_rate=.06,class_weight=weight,early_stopping=False,random_state=2028)
            model.fit(xs[0],ys[0]);joblib.dump(model,path)
        prob=model.predict_proba(xs[1])[:,1]
        threshold=policy(ys[1],prob,min_recall=previous_validation['recall'])
        report=metric_report(ys[1],prob,threshold) if threshold is not None else None
        results.append(dict(name=name,model=model,threshold=threshold,validation=report));print('VALIDATION',name,json.dumps(report),flush=True)
    viable=[r for r in results if r['validation'] and r['validation']['f1']>previous_validation['f1']]
    if not viable:raise ValueError('No validated improvement. Current model retained.')
    best=max(viable,key=lambda r:(r['validation']['f1'],r['validation']['precision']))
    # Final predictions are deliberately first computed after validation selection.
    newprob=best['model'].predict_proba(xs[2])[:,1];oldprob=old['model'].predict_proba(xs[2][:,old['feature_indices']])[:,1]
    reports={'Previous v2 (same fresh holdout)':metric_report(ys[2],oldprob,old['threshold']),'Sequence v4':metric_report(ys[2],newprob,best['threshold'])}
    protocol=dict(policy='Maximise validation F1 under 0.5% false-positive rate and recall at least V2 validation recall.',candidate=best['name'],validation_report=best['validation'],training='step <400; all fraud and every 24th legitimate original row',validation='steps 400–554; original row index modulo 8 =1',test='step >=555; original row index modulo 8 =3; disjoint from published V1/V2 tests; never used for selection',history='Sender/recipient context from retained observations. Six stream features computed from ALL strictly earlier original rows, without labels. No current/future row included.',limitations='Synthetic data. Same-hour file order assumed. Full-stream context may expose generator regularities. Replay uses trusted past-only source context snapshots; manual payments have observed-session context only. Scores are not calibrated; no real-bank claim.')
    bundle=dict(model=best['model'],feature_indices=list(range(23)),source='PaySim · sequence v4 · fresh holdout + full past stream',reports=reports,threshold=best['threshold'],test_rows=parts[2],seed_rows=parts[0]+parts[1],split=dict(train=len(parts[0]),validation=len(parts[1]),test=len(parts[2])),version='paysim-sequence-v4',protocol=protocol)
    manifest=dict(split=bundle['split'],protocol=protocol,validation_candidates=[dict(name=r['name'],validation=r['validation']) for r in results],reports=reports)
    joblib.dump(bundle,runtime/'sequence-model.joblib')
    # Deployment gate uses the already-fixed test evaluation only once.
    promoted=reports['Sequence v4']['f1']>reports['Previous v2 (same fresh holdout)']['f1']
    manifest['promoted']=promoted
    if promoted:
        joblib.dump(bundle,runtime/'next-model.joblib');os.replace(runtime/'next-model.joblib',runtime/'model.joblib')
        (runtime/'paysim-evaluation.json').write_text(json.dumps(manifest,indent=2))
    (runtime/'sequence-evaluation.json').write_text(json.dumps(manifest,indent=2));print('FINAL',json.dumps(manifest,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--runtime',default=str(Path(__file__).parent/'runtime'));args=p.parse_args();run(args.archive,Path(args.runtime))
