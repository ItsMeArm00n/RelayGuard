import io,json,os,platform,sqlite3,threading,time,csv
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse,Response
from fastapi.staticfiles import StaticFiles
import joblib
from engine import History,normalize,read_csv,sample_rows,train,predict
from explanations import ScoreExplainer,model_identity

ROOT=Path(__file__).parent;RUNTIME=Path(os.environ.get('RELAYGUARD_RUNTIME',ROOT/'runtime'));RUNTIME.mkdir(exist_ok=True,parents=True)
app=FastAPI(title='RelayGuard',version='0.1.0');lock=threading.RLock()
db=sqlite3.connect(RUNTIME/'events.sqlite',check_same_thread=False)
db.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, payload TEXT NOT NULL)');db.commit()
db.execute('CREATE TABLE IF NOT EXISTS archived_events (archive_id INTEGER PRIMARY KEY, id TEXT, payload TEXT NOT NULL)');db.commit()
bundle=joblib.load(RUNTIME/'model.joblib') if (RUNTIME/'model.joblib').exists() else train(sample_rows(),'Generated demo data — NOT PaySim')
identity=model_identity(bundle);explainer=None

def public_event(record):
    return {k:v for k,v in record.items() if k not in {'feature_snapshot','model_identity','explanation','_stream_context'}}
policy_path=RUNTIME/'policy.json'
def load_threshold():
    try:
        saved=json.loads(policy_path.read_text())
        value=float(saved['threshold'])
        if saved.get('version')==bundle['version'] and 0<value<1:return value
    except (OSError,ValueError,KeyError,TypeError):pass
    return bundle['threshold']
threshold=load_threshold();history=History();cursor=0;last_step=-1
events=[json.loads(r[0]) for r in db.execute('SELECT payload FROM events ORDER BY rowid')]
if any(r.get('version')!=bundle['version'] for r in events):
    # Preserve previous-model decisions while starting a clean, comparable replay.
    with db:
        db.executemany('INSERT INTO archived_events(id,payload) VALUES (?,?)',[(r['id'],json.dumps(r)) for r in events])
        db.execute('DELETE FROM events')
    events=[]
def rebuild():
    global history,cursor,last_step
    history=History()
    for r in bundle['seed_rows']:history.add(r)
    last_step=bundle['test_rows'][0]['step'] if bundle['test_rows'] else 0
    for r in events:history.add(r);last_step=max(last_step,r['step'])
    used={r['id'] for r in events};cursor=0
    while cursor<len(bundle['test_rows']) and bundle['test_rows'][cursor]['id'] in used:cursor+=1
rebuild()

def score(row,origin):
    global last_step
    started=time.perf_counter()
    if row['step']<last_step:raise ValueError(f'Out-of-order payment: use step {last_step} or later. Reset before replaying earlier events.')
    if db.execute('SELECT 1 FROM events WHERE id=?',(row['id'],)).fetchone():raise ValueError('Duplicate transaction ID.')
    x,reasons=history.features(row);risk=predict(bundle,x)
    record={k:v for k,v in row.items() if k not in {'isFraud','_stream_context'}}
    record['context_source']='Original past-only stream snapshot' if '_stream_context' in row else 'Observed session stream only (may be incomplete)'
    record.update(score=risk,flagged=risk>=threshold,threshold=threshold,reasons=reasons,review='Unreviewed',note='',origin=origin,version=bundle['version'],feature_snapshot=x,model_identity=identity,latency_ms=round((time.perf_counter()-started)*1000,2))
    db.execute('INSERT INTO events VALUES (?,?)',(record['id'],json.dumps(record)));db.commit()
    history.add(row);events.append(record);last_step=row['step'];return public_event(record)

@app.get('/api/state')
def state():
    with lock:return dict(source=bundle['source'],version=bundle['version'],threshold=threshold,events=[public_event(r) for r in reversed(events[-1000:])],count=len(events),alerts=sum(r['flagged'] for r in events),reviewed=sum(r['review']!='Unreviewed' for r in events),remaining=len(bundle['test_rows'])-cursor,last_step=last_step,reports=bundle['reports'],split=bundle['split'],protocol=bundle.get('protocol',{}),runtime=dict(machine=platform.machine(),system=platform.system(),linuxone_verified=False),notice='Local prototype. No authentication or real payment execution. Scores are not calibrated fraud probabilities.')

@app.get('/api/explain/{tx}')
def explain(tx:str):
    global explainer
    with lock:
        r=next((r for r in events if r['id']==tx),None)
        if r is None:raise HTTPException(404,'Transaction not found.')
        if 'feature_snapshot' not in r:raise HTTPException(409,'This payment was scored before explanations were enabled. Score a new payment to capture its original inputs.')
        if r.get('model_identity')!=identity:raise HTTPException(409,'The model has changed. An explanation cannot be recreated with a different model.')
        if r.get('explanation',{}).get('schema_version')!=1:
            try:
                if explainer is None:explainer=ScoreExplainer(bundle)
                r['explanation']=explainer.explain(r['feature_snapshot'],r['score'],r['threshold'],r['version'])
            except ValueError as e:raise HTTPException(409,str(e))
            db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(r),tx));db.commit()
        return r['explanation']

@app.get('/api/health')
def health():return dict(status='ok',model_version=bundle['version'],machine=platform.machine(),system=platform.system(),data_source=bundle['source'])

@app.post('/api/score')
def manual(data:dict):
    with lock:
        try:
            row=normalize(data)
            if row['amount']<=0:raise ValueError('Manual payment amount must be positive.')
            return score(row,'Manual test')
        except (ValueError,KeyError,TypeError) as e:raise HTTPException(400,str(e))

@app.post('/api/replay')
def replay():
    global cursor
    with lock:
        if cursor>=len(bundle['test_rows']):return dict(done=True)
        try:result=score(bundle['test_rows'][cursor],'Held-out replay')
        except ValueError as e:raise HTTPException(409,str(e))
        cursor+=1;return result

@app.post('/api/settings')
def settings(data:dict):
    global threshold
    with lock:
        try:
            value=float(data['threshold'])
            if not 0<value<1:raise ValueError('Threshold must be between 0 and 1.')
            policy_path.write_text(json.dumps(dict(version=bundle['version'],threshold=value)))
            threshold=value;return dict(threshold=threshold)
        except (ValueError,KeyError,TypeError) as e:raise HTTPException(400,str(e))

@app.post('/api/review/{tx}')
def review(tx:str,data:dict):
    with lock:
        if data.get('review') not in ['Needs investigation','Dismissed','Unreviewed']:raise HTTPException(400,'Invalid review decision.')
        r=next((r for r in events if r['id']==tx),None)
        if not r:raise HTTPException(404,'Transaction not found.')
        r.update(review=data['review'],note=str(data.get('note',''))[:1000]);db.execute('UPDATE events SET payload=? WHERE id=?',(json.dumps(r),tx));db.commit();return public_event(r)

@app.post('/api/reset')
def reset():
    with lock:events.clear();db.execute('DELETE FROM events');db.commit();rebuild();return dict(ok=True)

@app.post('/api/train')
async def upload(file:UploadFile=File(...)):
    global bundle,threshold,identity,explainer
    raw=await file.read(40_000_001)
    if len(raw)>40_000_000:raise HTTPException(400,'Upload limit: 40 MB.')
    try:rows=read_csv(raw.decode('utf-8-sig'));new=train(rows,'Uploaded labelled CSV — confirm PaySim provenance')
    except (ValueError,KeyError,UnicodeError) as e:raise HTTPException(400,str(e))
    with lock:
        joblib.dump(new,RUNTIME/'model.joblib');bundle=new;identity=model_identity(bundle);explainer=None;threshold=new['threshold'];events.clear();db.execute('DELETE FROM events');db.commit();rebuild()
    return dict(ok=True,split=bundle['split'])

@app.get('/api/export')
def export(archived:bool=False):
    with lock:
        out=io.StringIO();writer=csv.writer(out);writer.writerow(['id','step','type','amount','sender','recipient','score','flagged','review','note','model_version','threshold','explanation_method','explanation_summary'])
        records=[json.loads(row[0]) for row in db.execute('SELECT payload FROM archived_events ORDER BY archive_id')] if archived else events
        for r in records:
            cells=[r[k] for k in ['id','step','type','amount','sender','recipient','score','flagged','review','note']]
            cells.extend([r.get('version',''),r.get('threshold',''),r.get('explanation',{}).get('method',''),r.get('explanation',{}).get('summary','')])
            writer.writerow(["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for v in cells])
        return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=relayguard-review.csv'})

@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
