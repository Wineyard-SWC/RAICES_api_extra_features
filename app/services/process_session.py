import numpy as np
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import InterfaceError, DisconnectionError  # ✅ Agregar imports

from app.models.biometrics import SessionPayload
from app.db.models_bio import Session, Baseline, SessionTask
from app.services.signal_processing import (
    theta_beta_ratio, lf_hf_ratio, hr_from_ppg, nz
)
from app.services.valence_arousal import (
    arousal_feature, valence_feature
)
from app.services.emotion import emotion_from_axes


# ---------- helper para tomar canales por nombre -----------------
def pick(eeg_packets: list, name: str) -> List[float]:
    for pkt in eeg_packets:
        if pkt.channel == name:
            return pkt.values
    return []


# ✅ Agregar función para manejar reconexión de BD
async def safe_db_operation(operation_func):
    """Ejecuta operación de BD con reintentos en caso de desconexión"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            await operation_func()
            return  # Éxito
            
        except (InterfaceError, DisconnectionError) as e:
            print(f"Conexión perdida (intento {attempt + 1}/{max_retries}): {e}")
            
            if attempt == max_retries - 1:
                raise  # Último intento fallido
                
            # Esperar antes del siguiente intento
            import asyncio
            await asyncio.sleep(1)
            
        except Exception as e:
            # Otros errores no relacionados con conexión
            raise


# ---------- pipeline principal ----------------------------------
async def process_session(payload: SessionPayload, db: AsyncSession) -> None:
    try:
        # 1) sesión ----------------------------------------------------
        sess = Session(
            session_id       = payload.sessionId,
            user_firebase_id = payload.userFirebaseId,
            context_type     = payload.contextType,
            session_relation = payload.sessionRelation  # ✅ Incluir nuevo campo
        )
        db.add(sess)
        
        # ✅ Manejar reconexión en flush
        await safe_db_operation(db.flush)

        # 2) baseline --------------------------------------------------
        af7_rest   = pick(payload.restData.eeg, "AF7") or pick(payload.restData.eeg, "TP9")
        base_theta = nz(theta_beta_ratio(af7_rest))
        base_lf    = nz(lf_hf_ratio(payload.restData.ppg))
        base_hr    = nz(hr_from_ppg(payload.restData.ppg))

        # ✅ Verificar que tenemos al menos algunos valores válidos
        if base_hr == 0.0:
            print("⚠️  Warning: No se pudo calcular HR baseline, usando valor por defecto")
            base_hr = 70.0

        db.add(Baseline(
            session_id              = sess.session_id,
            baseline_eeg_theta_beta = base_theta,
            baseline_hrv_lf_hf      = base_lf,
            baseline_hr             = base_hr
        ))

        # 3) tareas ----------------------------------------------------
        task_records: List[Tuple[float, float]] = []
        stresses:     List[float]              = []

        for t in payload.tasks:
            af7 = pick(t.eeg, "AF7") or pick(t.eeg, "TP9")
            af8 = pick(t.eeg, "AF8")
            
            theta = nz(theta_beta_ratio(af7, is_task=True))
            asym  = nz(np.mean(af7) - np.mean(af8)) if af8 and af7 else 0.0

            lf = nz(lf_hf_ratio(t.ppg, is_task=True))
            
            # ✅ CAMBIO: Siempre calcular HR desde PPG
            hr_task = nz(hr_from_ppg(t.ppg, is_task=True)) if t.ppg else base_hr
            
            # Calcular diferencias
            d_theta = theta - base_theta
            d_lf    = lf    - base_lf
            d_hr    = hr_task - base_hr
            
            arousal = arousal_feature(d_theta, -d_lf, 0.0, d_hr)
            valence = valence_feature(asym)

            task_records.append((arousal, valence))
            stresses.append((arousal + 1) / 2)

            emotion_label, _ = emotion_from_axes(valence, arousal)

            db.add(SessionTask(
                session_id        = sess.session_id,
                task_id           = t.taskId,
                task_name         = t.taskName,
                normalized_stress = stresses[-1],
                emotion_label     = emotion_label,
                heart_rate        = hr_task  # ✅ Guardar el HR calculado
            ))

        # 4) resumen sesión -------------------------------------------
        if task_records:
            sess.session_arousal = float(np.mean([a for a, _ in task_records]))
            sess.session_valence = float(np.mean([v for _, v in task_records]))
            sess.session_emotion, _ = emotion_from_axes(
                sess.session_valence, sess.session_arousal
            )
            sess.session_avg_stress = float(np.mean(stresses))

        # ✅ Commit final con manejo de reconexión
        await safe_db_operation(db.commit)
        
    except Exception as e:
        print(f"Error procesando la sesión: {e}")
        await safe_db_operation(db.rollback)
        raise
