"""Exact grouped interventional Shapley values of the existing risk score.

Enumerates all coalitions of at most six semantic groups; no approximation,
LLM, external API or extra compiled dependency. Reference is empirical training
features, not a population fraud probability. Values explain model behaviour.
"""
import math,time
from itertools import combinations
import numpy as np
import joblib
from engine import History

GROUPS=[('amount','Payment amount',[0]),('type','Payment type',[1,2,3,4,5]),('sender','Sender history',[6,7,8,9]),('time','Simulation timing',[10,11,12]),('recipient','Recipient history',[13,14,15,16]),('stream','Recent payment stream',[17,18,19,20,21,22])]

def model_identity(bundle):return joblib.hash((bundle['model'],bundle.get('feature_indices',list(range(10)))))

def training_reference(bundle,count=32):
    rows=bundle['seed_rows'][:bundle['split']['train']]
    if not rows:raise ValueError('No training data available for an explanation reference.')
    selected=set(np.linspace(0,len(rows)-1,min(count,len(rows)),dtype=int).tolist())
    history=History();reference=[]
    for i,row in enumerate(rows):
        if i in selected:reference.append(history.features(row)[0])
        history.add(row)
    indices=bundle.get('feature_indices',list(range(10)))
    return np.asarray(reference,dtype=float)[:,indices]

class ScoreExplainer:
    def __init__(self,bundle):
        self.model=bundle['model'];self.identity=model_identity(bundle)
        self.indices=bundle.get('feature_indices',list(range(10)))
        self.reference=training_reference(bundle)
        self.groups=[]
        for key,label,indices in GROUPS:
            positions=[self.indices.index(i) for i in indices if i in self.indices]
            if positions:self.groups.append((key,label,positions))
        if set(i for _,_,g in self.groups for i in g)!=set(range(len(self.indices))):raise ValueError('Feature schema is not fully covered by the explanation groups.')

    def explain(self,features,score,threshold,version):
        started=time.perf_counter();x=np.asarray([features[i] for i in self.indices]);n=len(self.groups);m=len(self.reference)
        if x.shape!=(len(self.indices),) or not np.all(np.isfinite(x)):raise ValueError('Invalid saved feature snapshot.')
        coalitions=[]
        for mask in range(1<<n):
            batch=self.reference.copy()
            for i,(_,_,positions) in enumerate(self.groups):
                if mask&(1<<i):batch[:,positions]=x[positions]
            coalitions.append(batch)
        values=self.model.predict_proba(np.concatenate(coalitions))[:,1].reshape(1<<n,m).mean(axis=1)
        if not math.isclose(float(values[-1]),score,abs_tol=1e-8):raise ValueError('Saved score does not match this model and feature snapshot.')
        contributions=[]
        for i,(key,label,_) in enumerate(self.groups):
            phi=0.
            for mask in range(1<<n):
                if mask&(1<<i):continue
                k=mask.bit_count();weight=math.factorial(k)*math.factorial(n-k-1)/math.factorial(n)
                phi+=weight*(values[mask|(1<<i)]-values[mask])
            contributions.append(dict(key=key,label=label,value=float(phi),direction='increased' if phi>1e-9 else 'reduced' if phi< -1e-9 else 'neutral'))
        baseline=float(values[0]);reconstructed=baseline+sum(r['value'] for r in contributions)
        error=abs(reconstructed-score)
        if error>1e-8:raise ValueError('Explanation failed its score reconciliation check.')
        positive=sorted([r for r in contributions if r['value']>1e-9],key=lambda r:-r['value'])
        negative=sorted([r for r in contributions if r['value']< -1e-9],key=lambda r:r['value'])
        clauses=[]
        if positive:clauses.append(' and '.join(r['label'].lower() for r in positive[:2])+' raised the score')
        if negative:clauses.append(' and '.join(r['label'].lower() for r in negative[:2])+' lowered it')
        summary=('. '.join(c[0].upper()+c[1:] for c in clauses)+'. ') if clauses else 'These groups had no material effect relative to the reference. '
        summary+=f'The final score of {score:.4f} '+('met or exceeded' if score>=threshold else 'was below')+f' the recorded alert threshold of {threshold:.4f}; '+('review was suggested.' if score>=threshold else 'no alert was triggered.')
        return dict(schema_version=1,method='Exact grouped Shapley',output_space='Uncalibrated model risk score',baseline=baseline,score=score,threshold=threshold,contributions=contributions,reconstructed_score=reconstructed,reconciliation_error=error,reference_count=m,summary=summary,model_version=version,model_identity=self.identity,latency_ms=round((time.perf_counter()-started)*1000,2),reference_description=f'{m} evenly spaced training observations; class-enriched training reference for the archive model.',limitation='Explains this model relative to the training reference, not a cause or proof of fraud. Group masking can combine correlated transformed features in artificial ways. Scores and contributions are not fraud probabilities or percentage-point changes in real-world fraud risk.')
