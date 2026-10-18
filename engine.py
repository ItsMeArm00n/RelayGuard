import csv, math, random
import numpy as np
from collections import defaultdict,deque
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_score, recall_score, f1_score, confusion_matrix

TYPES=['PAYMENT','TRANSFER','CASH_OUT','CASH_IN','DEBIT']
def normalize(row, i=0):
    step=int(row['step']);amount=float(row['amount'])
    sender=str(row.get('sender',row.get('nameOrig',''))).strip()
    recipient=str(row.get('recipient',row.get('nameDest',''))).strip()
    kind=str(row['type']).upper()
    if step<0 or not math.isfinite(amount) or amount<0:raise ValueError('Step and amount must be non-negative; amount must be finite.')
    if kind not in TYPES:raise ValueError('Unsupported payment type.')
    if not sender or not recipient or sender==recipient:raise ValueError('Provide different sender and recipient IDs.')
    tx=str(row.get('id') or f'TX-{i+1:07d}').strip()
    if not tx or max(map(len,[tx,sender,recipient]))>100:raise ValueError('IDs must contain 1–100 characters.')
    label=row.get('isFraud')
    if label not in [None,'',0,1,'0','1']:raise ValueError('isFraud must be 0 or 1.')
    return dict(id=tx,step=step,type=kind,amount=amount,sender=sender,recipient=recipient,isFraud=None if label in [None,''] else int(label))

class StreamContext:
    """Label-free stream statistics, evaluated strictly before the current event."""
    def __init__(self):
        self.step=None;self.current=0;self.transfers=0;self.previous=0;self.previous_transfers=0
        self.recent=deque();self.amounts={}
    def advance(self,step):
        if self.step is not None and step<self.step:raise ValueError('Stream context requires chronological events.')
        if step!=self.step:
            contiguous=self.step is not None and step==self.step+1
            self.previous=self.current if contiguous else 0;self.previous_transfers=self.transfers if contiguous else 0
            self.current=0;self.transfers=0;self.step=step
        while self.recent and step-self.recent[0][0]>24:
            _,key=self.recent.popleft();self.amounts[key][0]-=1
            if self.amounts[key][0]==0:del self.amounts[key]
    def features(self,row):
        self.advance(row['step']);cents=round(row['amount']*100)
        transfer=self.amounts.get(('TRANSFER',cents),[0,row['step']-25])
        cashout=self.amounts.get(('CASH_OUT',cents),[0,0])
        return [math.log1p(self.previous),math.log1p(self.current),math.log1p(transfer[0]),min(25,row['step']-transfer[1]),math.log1p(cashout[0]),math.log1p(self.previous_transfers)]
    def add(self,row):
        self.advance(row['step']);self.current+=1
        if row['type']=='TRANSFER':self.transfers+=1
        if row['type'] in ['TRANSFER','CASH_OUT']:
            key=(row['type'],round(row['amount']*100));self.recent.append((row['step'],key))
            value=self.amounts.setdefault(key,[0,row['step']]);value[0]+=1;value[1]=row['step']

class History:
    def __init__(self):
        self.accounts=defaultdict(lambda:dict(count=0,total=0.,recipients=set()))
        self.receivers=defaultdict(lambda:dict(count=0,total=0.,senders=set()))
        self.stream=StreamContext()
    def features(self,row):
        a=self.accounts[row['sender']];n=a['count'];mean=a['total']/n if n else 0
        base=[math.log1p(row['amount'])]+[int(row['type']==t) for t in TYPES]
        history=[math.log1p(n),math.log1p(mean),math.log1p(row['amount']/(mean+1)),int(row['recipient'] not in a['recipients'])]
        reasons=[f"Payment type: {row['type']}"]
        if n==0:reasons.append('Limited history: first observed outgoing payment')
        else:
            reasons.append(f'{n} earlier outgoing payments; average amount {mean:,.2f}')
            if row['amount']>3*mean:reasons.append(f'Amount is {row["amount"]/max(mean,1):.1f}× the earlier account average')
        if row['recipient'] not in a['recipients']:reasons.append('Recipient not previously observed for this sender')
        receiver=self.receivers[row['recipient']]
        hour=row['step']%24
        context=[hour,math.sin(2*math.pi*hour/24),math.cos(2*math.pi*hour/24),math.log1p(receiver['count']),math.log1p(receiver['total']),math.log1p(len(receiver['senders'])),int(row['sender'] in receiver['senders'])]
        reasons.append(f'Simulation hour: {hour:02d} (relative dataset clock)')
        if receiver['count']:reasons.append(f"Recipient has {receiver['count']} earlier incoming payments in observed history")
        stream=row.get('_stream_context')
        if stream is None:stream=self.stream.features(row)
        if stream[2]>0:reasons.append('A transfer with the same amount was observed earlier within 24 simulation hours')
        return base+history+context+stream,reasons
    def add(self,row):
        a=self.accounts[row['sender']];a['count']+=1;a['total']+=row['amount'];a['recipients'].add(row['recipient'])
        b=self.receivers[row['recipient']];b['count']+=1;b['total']+=row['amount'];b['senders'].add(row['sender'])
        self.stream.add(row)

def predict(bundle,x):
    indices=bundle.get('feature_indices',list(range(10)))
    return float(bundle['model'].predict_proba([[x[i] for i in indices]])[0,1])

def metric_report(y,prob,threshold):
    pred=np.asarray(prob)>=threshold
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return dict(precision=float(precision_score(y,pred,zero_division=0)),recall=float(recall_score(y,pred,zero_division=0)),average_precision=float(average_precision_score(y,prob)),f1=float(f1_score(y,pred,zero_division=0)),threshold=float(threshold),tp=int(tp),fp=int(fp),fn=int(fn),tn=int(tn),test_count=len(y),test_fraud=int(sum(y)),false_positive_rate=float(fp/max(fp+tn,1)))

def select_threshold(y,prob,budget=.005):
    """Maximise recall with <= budget false positives, using validation data only."""
    from sklearn.metrics import roc_curve
    y=np.asarray(y);prob=np.asarray(prob)
    fpr,tpr,thresholds=roc_curve(y,prob,drop_intermediate=False)
    feasible=np.where((fpr<=budget)&np.isfinite(thresholds)&(thresholds>0)&(thresholds<1))[0]
    if not len(feasible):return float(np.nextafter(min(1.,max(prob)),1.))
    # Highest recall, then fewest false positives, then higher threshold.
    best=max(feasible,key=lambda i:(tpr[i],-fpr[i],thresholds[i]))
    return float(thresholds[best])

def sample_rows(n=3600):
    rng=random.Random(2026);rows=[]
    for i in range(n):
        sender=f'C{rng.randrange(100,190)}';kind=rng.choice(TYPES)
        amount=round(rng.lognormvariate(6.1,1.5),2)
        # Overlapping classes keep the illustrative generator from being a perfect rule.
        p=.015+(.28 if kind in ['TRANSFER','CASH_OUT'] and amount>2500 else 0)
        fraud=int(rng.random()<p)
        if fraud and rng.random()<.65:amount*=rng.uniform(2,6)
        rows.append(normalize(dict(id=f'DEMO-{i:05}',step=i//12,type=kind,amount=round(amount,2),sender=sender,recipient=f'C{rng.randrange(200,400)}',isFraud=fraud)))
    return rows

def train(rows,source):
    # Whole time steps stay in a single partition; IDs/outcomes never enter features.
    steps=sorted({r['step'] for r in rows})
    if len(steps)<10:raise ValueError('Provide at least ten distinct time steps.')
    a=steps[int(len(steps)*.6)];b=steps[int(len(steps)*.8)]
    parts=[[],[],[]];h=History()
    for r in rows:
        if r['isFraud'] is None:raise ValueError('Training CSV requires isFraud labels.')
        x,_=h.features(r);p=0 if r['step']<a else 1 if r['step']<b else 2
        parts[p].append((x,r['isFraud'],r));h.add(r)
    if any(len({r[1] for r in part})<2 for part in parts):raise ValueError('Each time partition must contain both fraud and legitimate transactions. Use a larger representative file.')
    models={};reports={}
    for name,indices in [('Transaction only',list(range(6))),('Time and account context',list(range(17)))]:
        model=HistGradientBoostingClassifier(max_iter=120,max_leaf_nodes=15,l2_regularization=5,class_weight='balanced',early_stopping=False,random_state=2026)
        features=lambda part:[[r[0][i] for i in indices] for r in part]
        model.fit(features(parts[0]),[r[1] for r in parts[0]])
        val=model.predict_proba(features(parts[1]))[:,1];vy=[r[1] for r in parts[1]]
        threshold=select_threshold(vy,val)
        prob=model.predict_proba(features(parts[2]))[:,1];y=[r[1] for r in parts[2]]
        reports[name]=metric_report(y,prob,threshold)
        models[name]=model
    active='Time and account context'
    return dict(model=models[active],feature_indices=list(range(17)),source=source,reports=reports,threshold=reports[active]['threshold'],test_rows=[r[2] for r in parts[2]],seed_rows=[r for r in rows if r['step']<b],split=dict(train=len(parts[0]),validation=len(parts[1]),test=len(parts[2])),version='upload-hgb-v2',protocol=dict(policy='Maximise validation recall under a 0.5% false-positive budget; test rates may differ.',candidate=active))

def read_csv(text):
    rows=[normalize(r,i) for i,r in enumerate(csv.DictReader(text.splitlines()))]
    if len(rows)<100:raise ValueError('Provide at least 100 labelled rows for training.')
    if len(rows)>150000:raise ValueError('Prototype limit: 150,000 rows. Prepare a chronological subset.')
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Transaction IDs must be unique.')
    return sorted(rows,key=lambda r:r['step'])
