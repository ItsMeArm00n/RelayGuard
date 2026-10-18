"""Validation-only V3 selection; fresh, label-independent final holdout."""
import os,argparse,json,csv,io,zipfile,time
from pathlib import Path
import numpy as np,joblib
from sklearn.ensemble import HistGradientBoostingClassifier,ExtraTreesClassifier,RandomForestClassifier
from sklearn.metrics import roc_curve
from engine import History,normalize,metric_report
from models import RiskEnsemble

def policy(y,prob,budget=.005,min_recall=0.):
    fpr,tpr,t=roc_curve(y,prob,drop_intermediate=False)
    positives=np.sum(y);negatives=len(y)-positives
    tp=tpr*positives;fp=fpr*negatives
    precision=tp/np.maximum(tp+fp,1)
    f1=2*precision*tpr/np.maximum(precision+tpr,1e-15)
    valid=np.where(np.isfinite(t)&(t>0)&(t<1)&(fpr<=budget)&(tpr>=min_recall))[0]
    if not len(valid):return None
    i=max(valid,key=lambda k:(f1[k],precision[k],tpr[k]))
    return float(t[i])

def load_data(archive,runtime):
    cache=runtime/'v3-data.joblib'
    if cache.exists():return joblib.load(cache)
    old=joblib.load(runtime/'v2-training-cache.joblib')
    training,validation=old['parts'][:2];test=[]
    with zipfile.ZipFile(archive) as z:
        name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
        with z.open(name) as f:
            for i,r in enumerate(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig'))):
                # Modulo 3 excludes prior v2 modulo-1 holdout and original modulo-0 rows.
                if int(r['step'])>=555 and i%8==3:
                    r['id']=f'PS-{i+1:07d}';test.append(normalize(r,i))
    parts=[training,validation,test];history=History();xs=[];ys=[]
    for part in parts:
        features=[]
        for row in part:
            x,_=history.features(row);features.append(x);history.add(row)
        xs.append(np.asarray(features,dtype=np.float32));ys.append(np.asarray([r['isFraud'] for r in part]))
    result=dict(parts=parts,x=xs,y=ys)
    joblib.dump(result,cache);return result

def run(archive,runtime):
    data=load_data(archive,runtime);xs=data['x'];ys=data['y'];parts=data['parts']
    baseline_path=runtime/'v2-model.joblib'
    if not baseline_path.exists():
        baseline=joblib.load(runtime/'model.joblib')
        if baseline['version']!='paysim-hgb-v2':raise ValueError('Need the preserved V2 model for this experiment.')
        joblib.dump(baseline,baseline_path)
    baseline=joblib.load(baseline_path)
    val0=baseline['model'].predict_proba(xs[1][:,baseline['feature_indices']])[:,1]
    report0=metric_report(ys[1],val0,baseline['threshold'])
    minimum_recall=report0['recall'];print('Incumbent validation:',json.dumps(report0),flush=True)
    definitions=[
        ('Fine boosted trees',HistGradientBoostingClassifier(max_iter=350,max_leaf_nodes=31,max_depth=8,min_samples_leaf=20,l2_regularization=1,learning_rate=.05,early_stopping=False,random_state=2027)),
        ('Weighted boosted trees',HistGradientBoostingClassifier(max_iter=450,max_leaf_nodes=31,max_depth=10,min_samples_leaf=15,l2_regularization=2,learning_rate=.05,class_weight={0:1,1:3},early_stopping=False,random_state=2027)),
        ('Extra trees',ExtraTreesClassifier(n_estimators=200,max_depth=24,min_samples_leaf=3,max_features=1.,class_weight='balanced',n_jobs=2,random_state=2027)),
        ('Random forest',RandomForestClassifier(n_estimators=160,max_depth=20,min_samples_leaf=2,max_features=.8,class_weight='balanced_subsample',bootstrap=True,max_samples=.8,n_jobs=2,random_state=2027))]
    fitted={};results=[]
    for name,model in definitions:
        modelpath=runtime/('v3-'+name.lower().replace(' ','-')+'.joblib')
        if modelpath.exists():model=joblib.load(modelpath)
        else:
            start=time.time();model.fit(xs[0],ys[0]);joblib.dump(model,modelpath)
            print('Fitted',name,'seconds',round(time.time()-start,1),flush=True)
        fitted[name]=model
        prob=model.predict_proba(xs[1])[:,1]
        t=policy(ys[1],prob,min_recall=minimum_recall)
        report=metric_report(ys[1],prob,t) if t is not None else None
        results.append(dict(name=name,model=model,threshold=t,validation=report))
        print('Validation',name,json.dumps(report),flush=True)
    for name,names in [('Boost + forest',['Weighted boosted trees','Random forest']),('Boost + extra trees',['Weighted boosted trees','Extra trees'])]:
        model=RiskEnsemble([fitted[n] for n in names]);prob=model.predict_proba(xs[1])[:,1]
        t=policy(ys[1],prob,min_recall=minimum_recall)
        report=metric_report(ys[1],prob,t) if t is not None else None
        results.append(dict(name=name,model=model,threshold=t,validation=report))
        print('Validation',name,json.dumps(report),flush=True)
    viable=[r for r in results if r['validation'] is not None]
    if not viable:raise ValueError('No candidate meets the validation recall/false-positive constraints; V2 retained.')
    best=max(viable,key=lambda r:(r['validation']['f1'],r['validation']['precision']))
    if best['validation']['f1']<=report0['f1']:raise ValueError('Validation F1 did not improve; V2 retained.')
    # Final test is first inspected only after committing to the chosen model/policy.
    prob=best['model'].predict_proba(xs[2])[:,1]
    oldprob=baseline['model'].predict_proba(xs[2][:,baseline['feature_indices']])[:,1]
    reports={'Previous v2 (same fresh holdout)':metric_report(ys[2],oldprob,baseline['threshold']),'Improved v3':metric_report(ys[2],prob,best['threshold'])}
    protocol=dict(policy='Maximise validation F1 with <=0.5% legitimate-payment false positives and recall at least the V2 validation recall.',training='Unchanged V2 training: step <400, all fraud plus every 24th original legitimate row.',validation='Unchanged V2 validation: steps 400–554, zero-based row index modulo 8 =1.',test='Fresh rows: step >=555, zero-based original row index modulo 8 =3; disjoint from earlier V1/V2 holdouts.',candidate=best['name'],validation_report=best['validation'],previous_validation=report0,limitations='Synthetic data; sampled and class-enriched history; simulation timing may reflect generator artefacts. Final test labels not used for candidate or threshold selection. Different holdouts mean prior published percentages are not directly comparable.')
    manifest=dict(split=dict(train=len(parts[0]),validation=len(parts[1]),test=len(parts[2])),protocol=protocol,validation_candidates=[dict(name=r['name'],validation=r['validation']) for r in results],reports=reports)
    bundle=dict(model=best['model'],feature_indices=list(range(17)),source='PaySim · improved v3 · fresh unseen-row evaluation',reports=reports,threshold=best['threshold'],test_rows=parts[2],seed_rows=parts[0]+parts[1],split=manifest['split'],version='paysim-ensemble-v3',protocol=protocol)
    joblib.dump(bundle,runtime/'v3-next-model.joblib');os.replace(runtime/'v3-next-model.joblib',runtime/'model.joblib')
    (runtime/'paysim-evaluation.json').write_text(json.dumps(manifest,indent=2))
    print('FINAL',json.dumps(manifest,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('--runtime',default=str(Path(__file__).parent/'runtime'));args=p.parse_args();run(args.archive,Path(args.runtime))
