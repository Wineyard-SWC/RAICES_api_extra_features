# app/services/emotion.py
from typing import Tuple

# ───── 1) Mapa limpio  ─────────────────────────────────────────────
EMOTION_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ('strong_pos', 'low'):      ('Relaxed',   '😌'),
    ('strong_pos', 'moderate'): ('Happy',     '😁'),
    ('strong_pos', 'high'):     ('Euphoric',  '🤯'),

    ('pos', 'low'):             ('Calm',      '😌'),
    ('pos', 'high'):            ('Excited',   '🤩'),

    ('neg', 'low'):             ('Sad',       '😢'),
    ('neg', 'high'):            ('Stressed',  '😰'),
}

DEFAULT_EMOTION = ('Neutral', '😐')


# ───── 2) Categorizar valence & arousal  ───────────────────────────
def cat_valence(v: float) -> str:
    if v < -0.5:
        return 'strong_neg'
    if -0.5 <= v < 0:
        return 'neg'
    if 0 <= v < 0.5:
        return 'pos'
    return 'strong_pos'


def cat_arousal(a: float) -> str:
    if a < -0.25:
        return 'low'
    if -0.25 <= a < 0.25:
        return 'moderate'
    return 'high'


# ───── 3) Elegir etiqueta & emoji  ─────────────────────────────────
def emotion_from_axes(valence: float, arousal: float) -> tuple[str, str]:
    pair = (cat_valence(valence), cat_arousal(arousal))
    return EMOTION_MAP.get(pair, DEFAULT_EMOTION)
