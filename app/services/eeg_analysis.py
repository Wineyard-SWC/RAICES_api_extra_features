# app/services/eeg_analysis.py
import numpy as np

def detect_emotion_from_eeg(raw_data: list):
    """
    Recibe la data EEG proveniente de Muse en formato:
    [
      {"electrode": 2, "timestamp": 1689094456.056, "samples": [398, 415, 420]},
      {"electrode": 3, "timestamp": 1689094456.062, "samples": [422, 419, 412]},
      ...
    ]
    Retorna la emoción detectada (ej.: "Feliz", "Estresado", etc.) y el emoji.
    """

    # 1) Acumular muestras por electrodo
    electrode_data = {0: [], 1: [], 2: [], 3: []}
    for entry in raw_data:
        elec = entry['electrode']
        samples = entry['samples']
        electrode_data[elec].extend(samples)

    # 2) Calcular potencias "naif" en bandas Alpha y Theta
    alpha_af7 = np.mean(electrode_data[1]) if electrode_data[1] else 0
    alpha_af8 = np.mean(electrode_data[2]) if electrode_data[2] else 0

    theta_af7 = alpha_af7 * 0.8
    theta_af8 = alpha_af8 * 0.8

    alpha_avg = np.mean([alpha_af7, alpha_af8]) if (alpha_af7 or alpha_af8) else 0
    theta_avg = np.mean([theta_af7, theta_af8]) if (theta_af7 or theta_af8) else 0
    theta_alpha_ratio = theta_avg / alpha_avg if alpha_avg != 0 else np.nan

    asym_index = alpha_af8 - alpha_af7  # (AF8 - AF7)

    # 3) Clasificación de valencia y activación
    # Valencia (según asimetría)
    if asym_index < -1:
        valence_cat = 'strong_pos'
    elif -1 <= asym_index < 0:
        valence_cat = 'pos'
    elif 0 <= asym_index < 1:
        valence_cat = 'neg'
    else:
        valence_cat = 'strong_neg'

    # Activación (según ratio Theta/Alpha)
    if np.isnan(theta_alpha_ratio):
        arousal_cat = 'none'
    elif theta_alpha_ratio < 0.8:
        arousal_cat = 'low'
    elif 0.8 <= theta_alpha_ratio < 1.2:
        arousal_cat = 'moderate'
    else:
        arousal_cat = 'high'

    # 4) Mapeo de (valencia, arousal) a emoción
    emotion_map = {
        ('strong_pos', 'low'):      ('Relaxed',   '😌'),
        ('strong_pos', 'moderate'): ('Happy',      '😁'),
        ('strong_pos', 'high'):     ('Euphoric',   '🤯'),

        ('pos', 'low'):             ('Calm',       '😌'),
        ('pos', 'moderate'):        ('Content',    '🙂'),
        ('pos', 'high'):            ('Excited',    '🤩'),

        ('neg', 'low'):             ('Sad',        '😢'),
        ('neg', 'moderate'):        ('Worried',    '😟'),
        ('neg', 'high'):            ('Stressed',   '😰'),

        ('strong_neg', 'low'):      ('Depressed',  '😞'),
        ('strong_neg', 'moderate'): ('Angry',      '😡'),
        ('strong_neg', 'high'):     ('Furious',    '🤬'),
    }

    emotion, emoji_ = emotion_map.get((valence_cat, arousal_cat), ('Neutral', '😐'))

    return emotion, emoji_
