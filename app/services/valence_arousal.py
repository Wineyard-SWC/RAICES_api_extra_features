# app/services/valence_arousal.py
from math import tanh
from statistics import mean

from math import tanh
from statistics import mean
import numpy as np

def z(val: float, std: float) -> float:
    """Z-score capado (NaN→0)."""
    return 0.0 if std == 0 or np.isnan(val) else val / std


def arousal_feature(d_theta: float, d_hrv: float, d_gsr: float, d_hr: float) -> float:
    feats = [
        -z(d_theta, 0.2),   # ↑β ⇒ +arousal
        -z(d_hrv,  0.5),    # ↓HRV ⇒ +arousal
        z(d_gsr,   0.3),    # +sudor ⇒ +arousal
        z(d_hr,    5.0),    # +BPM  ⇒ +arousal
    ]
    return tanh(mean(feats))   # rango (-1,1)


def valence_feature(asym: float) -> float:
    """Asimetría frontal → valence (-1…+1)."""
    return tanh(asym / 20.0)
