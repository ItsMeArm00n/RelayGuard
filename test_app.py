import os,tempfile,unittest,csv,io
from pathlib import Path
os.environ['RELAYGUARD_RUNTIME']=tempfile.mkdtemp(prefix='relayguard-tests-')
from fastapi.testclient import TestClient
from app import app
from engine import History,StreamContext,normalize,sample_rows,train,select_threshold,metric_report,predict
from explanations import ScoreExplainer,training_reference
from train_v3 import policy
from models import RiskEnsemble
import numpy as np

class KnownScoreModel:
    def predict_proba(self,x):
        x=np.asarray(x);p=.1+.02*x[:,0]+.04*x[:,2]
        return np.column_stack([1-p,p])

class WorkflowTests(unittest.TestCase):
    def setUp(self):self.c=TestClient(app);self.c.post('/api/reset')
    def test_stream_context_is_past_only_and_expires(self):
        s=StreamContext();a=normalize(dict(step=1,type='TRANSFER',amount=123.45,sender='A',recipient='B'))
        self.assertEqual(s.features(a)[2],0)
        s.add(a)
        b=normalize(dict(step=2,type='CASH_OUT',amount=123.45,sender='C',recipient='D'))
        x=s.features(b);self.assertGreater(x[2],0);self.assertEqual(x[3],1);self.assertGreater(x[0],0)
        self.assertEqual(s.features({**b,'step':26})[2],0)
        injected=normalize({**a,'_stream_context':[999]*6})
        self.assertNotIn('_stream_context',injected)
    def test_replay_review_export_and_duplicate(self):
        r=self.c.post('/api/replay').json();self.assertIn('score',r);self.assertNotIn('isFraud',r)
        duplicate=self.c.post('/api/score',json={k:r[k] for k in ['id','step','amount','type','sender','recipient']});self.assertEqual(duplicate.status_code,400)
        self.assertEqual(self.c.post('/api/review/'+r['id'],json={'review':'Needs investigation','note':'Check recipient'}).status_code,200)
        self.assertIn('Check recipient',self.c.get('/api/export').text)
        self.assertEqual(self.c.get('/api/state').json()['reviewed'],1)
    def test_inputs_and_order(self):
        s=self.c.get('/api/state').json();row=dict(id='TEST',step=s['last_step'],amount=1,type='PAYMENT',sender='A',recipient='B')
        self.assertEqual(self.c.post('/api/score',json={**row,'amount':-1}).status_code,400)
        self.assertEqual(self.c.post('/api/score',json={**row,'step':s['last_step']-1}).status_code,400)
        self.assertEqual(self.c.post('/api/settings',json={'threshold':2}).status_code,400)
        self.assertEqual(self.c.post('/api/review/missing',json={'review':'Dismissed'}).status_code,404)
    def test_no_label_or_outcome_leakage(self):
        h=History();r=normalize(dict(step=1,amount=10,type='TRANSFER',sender='A',recipient='B',isFraud=1))
        a,_=h.features(r);b,_=h.features({**r,'isFraud':0,'newbalanceOrig':100000})
        self.assertEqual(a,b);self.assertEqual(a[6],0);h.add(r);self.assertGreater(h.features(r)[0][6],0)
        self.assertEqual(a[13],0);self.assertGreater(h.features(r)[0][13],0)
    def test_threshold_budget_and_health(self):
        y=[0]*1000+[1]*10;prob=[.01]*995+[.6]*5+[.8]*8+[.2]*2
        t=select_threshold(y,prob);report=metric_report(y,prob,t)
        self.assertLessEqual(report['false_positive_rate'],.005)
        self.assertEqual(report['recall'],1)
        self.assertEqual(self.c.get('/api/health').json()['status'],'ok')
        self.assertEqual(self.c.post('/api/settings',json={'threshold':.876543}).status_code,200)
        from app import load_threshold
        self.assertEqual(load_threshold(),.876543)
    def test_csv_training_and_split(self):
        rows=sample_rows();f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
        result=self.c.post('/api/train',files={'file':('test.csv',f.getvalue(),'text/csv')})
        self.assertEqual(result.status_code,200,result.text)
        s=self.c.get('/api/state').json();self.assertEqual(s['count'],0);self.assertEqual(sum(s['split'].values()),len(rows))
        self.assertEqual(self.c.post('/api/replay').status_code,200)
    def test_explanation_reconciles_and_keeps_decision_snapshot(self):
        r=self.c.post('/api/replay').json()
        response=self.c.get('/api/explain/'+r['id']);self.assertEqual(response.status_code,200,response.text)
        explanation=response.json()
        self.assertAlmostEqual(explanation['baseline']+sum(x['value'] for x in explanation['contributions']),r['score'],places=8)
        self.assertLess(explanation['reconciliation_error'],1e-8)
        self.assertNotIn('feature_snapshot',r)
        self.assertNotIn('feature_snapshot',self.c.get('/api/state').json()['events'][0])
        self.c.post('/api/settings',json={'threshold':.123456})
        self.c.post('/api/replay')
        self.assertEqual(explanation,self.c.get('/api/explain/'+r['id']).json())
    def test_explanation_refuses_missing_or_changed_inputs(self):
        from app import events
        r=self.c.post('/api/replay').json()
        saved=events[-1].pop('feature_snapshot')
        self.assertEqual(self.c.get('/api/explain/'+r['id']).status_code,409)
        events[-1]['feature_snapshot']=saved;events[-1]['model_identity']='different-model'
        self.assertEqual(self.c.get('/api/explain/'+r['id']).status_code,409)
        self.assertEqual(self.c.get('/api/explain/missing').status_code,404)
    def test_known_model_group_effects_and_training_only_reference(self):
        rows=sample_rows(120)
        bundle=dict(model=KnownScoreModel(),feature_indices=list(range(17)),seed_rows=rows,split={'train':80})
        reference=training_reference(bundle)
        changed={**bundle,'seed_rows':rows[:80]+list(reversed(rows[80:]))}
        np.testing.assert_array_equal(reference,training_reference(changed))
        row=normalize(dict(step=20,type='TRANSFER',amount=99999,sender='A',recipient='B'))
        x,_=History().features(row);score=float(bundle['model'].predict_proba([x])[0,1])
        explanation=ScoreExplainer(bundle).explain(x,score,.5,'known-model')
        groups={g['key']:g['value'] for g in explanation['contributions']}
        self.assertGreater(groups['amount'],0)
        self.assertGreater(groups['type'],0)
        for key in ['sender','time','recipient']:self.assertAlmostEqual(groups[key],0,places=10)
    def test_v3_policy_constraints_and_ensemble_explanation(self):
        y=np.array([0]*1000+[1]*10);prob=np.array([.01]*995+[.6]*5+[.8]*8+[.2]*2)
        t=policy(y,prob,min_recall=.8);report=metric_report(y,prob,t)
        self.assertGreaterEqual(report['recall'],.8);self.assertLessEqual(report['false_positive_rate'],.005)
        self.assertIsNone(policy(y,prob,min_recall=1.1))
        rows=sample_rows(120);bundle=dict(model=RiskEnsemble([KnownScoreModel(),KnownScoreModel()]),feature_indices=list(range(17)),seed_rows=rows,split={'train':80})
        x,_=History().features(rows[-1]);score=predict(bundle,x)
        result=ScoreExplainer(bundle).explain(x,score,.5,'test-ensemble')
        self.assertAlmostEqual(result['reconstructed_score'],score,places=8)

if __name__=='__main__':unittest.main()
