"""Portable CPU-only model composition used by the V3 experiment."""
import numpy as np

class RiskEnsemble:
    def __init__(self,models):self.models=models
    def predict_proba(self,x):return np.mean([model.predict_proba(x) for model in self.models],axis=0)
