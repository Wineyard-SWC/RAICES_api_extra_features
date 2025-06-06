import numpy as np
import neurokit2 as nk
from brainflow.data_filter import (
    DataFilter, DetrendOperations, WindowOperations
)

# ───── Constantes ────────────────────────────────────────────────
SAMPLING_EEG = 256   # Muse-2
SAMPLING_PPG = 64    # Muse-2

# ───── Utilidades ────────────────────────────────────────────────
def safe_div(num: float, den: float) -> float:
    """Divide evitando 0/0 y NaN."""
    if not den or np.isnan(num) or np.isnan(den):
        return 0.0
    return num / den

def nz(x: float | None) -> float:
    """Convierte None/NaN a 0."""
    return 0.0 if x is None or np.isnan(x) else float(x)


# ───── Funciones EEG / PPG ───────────────────────────────────────
def theta_beta_ratio(eeg: list, is_task=False) -> float:
    """θ/β usando PSD-Welch; umbral menor para tareas"""
    if not eeg or len(eeg) == 0:
        return 0.0

    try:
        data = np.asarray(eeg, dtype=np.float64)
        data_len = len(data)
        
        # ✅ Umbrales diferentes para baseline vs tareas
        min_samples = 256 if is_task else 512  # 1s vs 2s
        
        print(f"Debug: Datos EEG - Longitud: {data_len}, Modo: {'tarea' if is_task else 'baseline'}")
        
        if data_len < min_samples:
            print(f"Datos insuficientes: {data_len} < {min_samples}")
            return 0.0

        # Remover valores NaN/inf
        data = data[~np.isnan(data)]
        data = data[~np.isinf(data)]
        
        if len(data) < min_samples:
            print("Datos insuficientes después de limpiar NaN/inf")
            return 0.0

        # Quitar tendencia
        DataFilter.detrend(data, DetrendOperations.LINEAR.value)

        # ✅ Parámetros adaptativos según cantidad de datos
        if is_task and len(data) < 512:
            nfft = 256      # Ventana más pequeña para tareas cortas
            overlap = 128   # 50% overlap
        else:
            nfft = 512      # Ventana normal para baseline
            overlap = 256   # 50% overlap
        
        # Verificar que tenemos suficientes datos para los parámetros elegidos
        if len(data) < nfft:
            print(f"Datos insuficientes para nfft: {len(data)} < {nfft}")
            return 0.0
            
        print(f"Debug: Parámetros PSD - nfft: {nfft}, overlap: {overlap}")

        # PSD con Welch
        try:
            psd, freq_res = DataFilter.get_psd_welch(
                data,
                nfft,
                overlap,
                SAMPLING_EEG,
                1  # BLACKMAN_HARRIS
            )
            print(f"Debug: PSD calculado - Longitud: {len(psd)}")
        except Exception as psd_error:
            print(f"Error en get_psd_welch: {psd_error}")
            return 0.0

        # Calcular bandas (igual que antes)
        try:
            freqs = np.arange(len(psd)) * freq_res
            theta_mask = (freqs >= 4.0) & (freqs <= 8.0)
            beta_mask = (freqs >= 15.0) & (freqs <= 30.0)
            
            theta_power = np.trapz(psd[theta_mask], freqs[theta_mask]) if np.any(theta_mask) else 0.0
            beta_power = np.trapz(psd[beta_mask], freqs[beta_mask]) if np.any(beta_mask) else 0.0
            
            if beta_power > 0:
                ratio = theta_power / beta_power
                print(f"Debug: Theta/Beta ratio: {ratio}")
                return float(ratio)
            else:
                return 0.0
                
        except Exception as band_error:
            print(f"Error calculando bandas: {band_error}")
            return 0.0
        
    except Exception as e:
        print(f"Error general: {e}")
        return 0.0


def hr_from_ppg(ppg: list, is_task=False) -> float:
    """Calcula heart rate desde PPG con manejo robusto de datos cortos"""
    min_samples = 64 if is_task else 128  # ~1s vs ~2s
    
    if not ppg or len(ppg) < min_samples:
        print(f"PPG datos insuficientes para HR: {len(ppg) if ppg else 0} < {min_samples}")
        return 0.0
        
    try:
        # Limpiar datos
        ppg_clean = [x for x in ppg if x is not None and not np.isnan(x) and not np.isinf(x)]
        if len(ppg_clean) < min_samples:
            print(f"PPG datos insuficientes para HR después de limpiar: {len(ppg_clean)} muestras")
            return 0.0
            
        print(f"Debug: Calculando HR desde PPG - {len(ppg_clean)} muestras")
        
        # ✅ Para datos muy cortos, usar método alternativo más simple
        if len(ppg_clean) < 200:  # < 3 segundos
            print(f"Datos PPG cortos ({len(ppg_clean)} muestras), usando método simple")
            return simple_hr_estimation(ppg_clean)
        
        # Método completo con NeuroKit2
        sig, info = nk.ppg_process(ppg_clean, sampling_rate=SAMPLING_PPG)
        peaks = info["PPG_Peaks"]
        
        if len(peaks) < 2:
            print("No hay suficientes picos, probando método simple")
            return simple_hr_estimation(ppg_clean)
            
        # Calcular intervalos RR en segundos
        rr_intervals = np.diff(peaks) / SAMPLING_PPG
        
        # Filtrar intervalos anómalos (300ms - 2000ms)
        valid_rr = rr_intervals[(rr_intervals > 0.3) & (rr_intervals < 2.0)]
        
        if len(valid_rr) == 0:
            print("No hay intervalos RR válidos, probando método simple")
            return simple_hr_estimation(ppg_clean)
        
        # Heart rate promedio
        mean_rr = np.mean(valid_rr)
        hr = 60.0 / mean_rr if mean_rr > 0 else 0.0
        
        print(f"Debug: HR calculado: {hr} bpm")
        return float(hr)
        
    except Exception as e:
        print(f"Error en hr_from_ppg: {e}")
        print("Probando método simple como fallback")
        return simple_hr_estimation(ppg_clean if 'ppg_clean' in locals() else ppg)


def simple_hr_estimation(ppg_data: list) -> float:
    """Estimación simple de HR usando detección básica de picos"""
    try:
        if len(ppg_data) < 64:  # < 1 segundo
            return 0.0
            
        data = np.array(ppg_data, dtype=float)
        
        # Normalizar datos
        data = (data - np.mean(data)) / np.std(data)
        
        # Detección simple de picos
        from scipy.signal import find_peaks
        
        # Buscar picos con threshold adaptativo
        threshold = 0.5 * np.std(data)
        min_distance = int(SAMPLING_PPG * 0.4)  # Mínimo 400ms entre picos
        
        peaks, _ = find_peaks(data, height=threshold, distance=min_distance)
        
        if len(peaks) < 2:
            print(f"Muy pocos picos encontrados: {len(peaks)}")
            return 0.0
        
        # Calcular HR basado en intervalos entre picos
        peak_intervals = np.diff(peaks) / SAMPLING_PPG  # En segundos
        
        # Filtrar intervalos válidos
        valid_intervals = peak_intervals[(peak_intervals > 0.4) & (peak_intervals < 2.0)]
        
        if len(valid_intervals) == 0:
            return 0.0
            
        mean_interval = np.mean(valid_intervals)
        hr = 60.0 / mean_interval
        
        print(f"Debug: HR simple calculado: {hr} bpm con {len(peaks)} picos")
        return float(hr)
        
    except Exception as e:
        print(f"Error en estimación simple: {e}")
        return 0.0


def lf_hf_ratio(ppg: list, is_task=False) -> float:
    """LF/HF con cálculo manual cuando NeuroKit2 falla"""
    min_samples = 128 if is_task else 192
    
    if not ppg or len(ppg) < min_samples:
        print(f"PPG datos insuficientes para LF/HF: {len(ppg) if ppg else 0} < {min_samples}")
        return 0.0

    try:
        # Limpiar datos PPG
        ppg_clean = [x for x in ppg if x is not None and not np.isnan(x) and not np.isinf(x)]
        
        if len(ppg_clean) < min_samples:
            print(f"PPG datos insuficientes para LF/HF después de limpiar: {len(ppg_clean)} muestras")
            return 0.0

        print(f"Debug: Procesando PPG para LF/HF - {len(ppg_clean)} muestras")
        
        sig, info = nk.ppg_process(ppg_clean, sampling_rate=SAMPLING_PPG)
        
        if "PPG_Peaks" not in info or len(info["PPG_Peaks"]) < 5:
            print("No se encontraron suficientes picos PPG para HRV")
            return 0.0

        # ✅ NUEVO: Calcular LF/HF manualmente
        peaks = info["PPG_Peaks"]
        
        # Calcular intervalos RR en milisegundos
        rr_intervals = np.diff(peaks) / SAMPLING_PPG * 1000  # En ms
        
        # Filtrar intervalos válidos
        valid_rr = rr_intervals[(rr_intervals > 300) & (rr_intervals < 2000)]
        
        if len(valid_rr) < 10:  # Necesitamos al menos 10 intervalos
            print(f"Muy pocos intervalos RR válidos: {len(valid_rr)}")
            return calculate_simple_lf_hf(valid_rr) if len(valid_rr) >= 3 else 0.0
        
        # ✅ Intentar primero con NeuroKit2
        try:
            hrv = nk.hrv(peaks, sampling_rate=SAMPLING_PPG, show=False)
            
            if not hrv.empty and "HRV_LFHF" in hrv.columns:
                value = hrv.loc[0, "HRV_LFHF"]
                print(f"Debug: LF/HF de NeuroKit2: {value}")
                
                if not np.isnan(value) and value > 0:
                    return float(value)
            
            # ✅ Si NeuroKit2 falla, calcular manualmente
            print("NeuroKit2 LF/HF inválido, calculando manualmente...")
            return calculate_manual_lf_hf(valid_rr)
            
        except Exception as nk_error:
            print(f"Error en NeuroKit2 HRV: {nk_error}")
            return calculate_manual_lf_hf(valid_rr)
        
    except Exception as e:
        print(f"Error en lf_hf_ratio: {e}")
        return 0.0


def calculate_manual_lf_hf(rr_intervals: np.ndarray) -> float:
    """Cálculo manual de LF/HF usando análisis espectral simple"""
    try:
        if len(rr_intervals) < 10:
            return 0.0
            
        # Interpolar RR intervals para obtener una señal uniforme
        from scipy.interpolate import interp1d
        from scipy.signal import welch
        
        # Crear timestamps
        time_rr = np.cumsum(rr_intervals) / 1000.0  # En segundos
        time_uniform = np.arange(0, time_rr[-1], 0.25)  # 4 Hz sampling
        
        if len(time_uniform) < 20:  # Muy corto para análisis espectral
            return calculate_simple_lf_hf(rr_intervals)
            
        # Interpolar
        f_interp = interp1d(time_rr[:-1], rr_intervals[:-1], kind='linear', 
                           bounds_error=False, fill_value='extrapolate')
        rr_uniform = f_interp(time_uniform)
        
        # Análisis espectral con Welch
        freqs, psd = welch(rr_uniform, fs=4.0, nperseg=min(16, len(rr_uniform)//2))
        
        # Definir bandas HRV
        lf_band = (freqs >= 0.04) & (freqs <= 0.15)  # LF: 0.04-0.15 Hz
        hf_band = (freqs >= 0.15) & (freqs <= 0.4)   # HF: 0.15-0.4 Hz
        
        # Calcular potencias
        lf_power = np.trapz(psd[lf_band], freqs[lf_band]) if np.any(lf_band) else 0.0
        hf_power = np.trapz(psd[hf_band], freqs[hf_band]) if np.any(hf_band) else 0.0
        
        if hf_power > 0:
            lf_hf = lf_power / hf_power
            print(f"Debug: LF/HF manual calculado: {lf_hf} (LF: {lf_power:.3f}, HF: {hf_power:.3f})")
            return float(lf_hf)
        else:
            return calculate_simple_lf_hf(rr_intervals)
            
    except Exception as e:
        print(f"Error en cálculo manual LF/HF: {e}")
        return calculate_simple_lf_hf(rr_intervals)


def calculate_simple_lf_hf(rr_intervals: np.ndarray) -> float:
    """LF/HF simplificado basado en variabilidad temporal"""
    try:
        if len(rr_intervals) < 3:
            return 0.0
            
        # Usar desviación estándar como proxy de variabilidad
        rr_std = np.std(rr_intervals)
        rr_mean = np.mean(rr_intervals)
        
        # Calcular coeficiente de variación escalado
        cv = (rr_std / rr_mean) if rr_mean > 0 else 0.0
        
        # Escalarlo a un rango razonable (típicamente LF/HF está entre 0.5 y 4.0)
        lf_hf_proxy = cv * 50  # Factor de escala empírico
        
        print(f"Debug: LF/HF simple calculado: {lf_hf_proxy} (CV: {cv:.4f})")
        return min(max(float(lf_hf_proxy), 0.1), 10.0)  # Limitar entre 0.1 y 10.0
        
    except Exception as e:
        print(f"Error en LF/HF simple: {e}")
        return 0.0