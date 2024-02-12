import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def fourier_analysis(df, time_interval, new_set=None, custom_interval=None):
    # Verifica se l'indice è di tipo datetime.date e converte se necessario
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, format="%Y-%m-%dT%H:%M:%S")

    timestamps = pd.to_numeric(df.index.values) // 10**9  # Converti in secondi
    timestamps -= timestamps.min()  # Normalizza rispetto al tempo zero
    
    
    # Calcola la frequenza campionaria
    fs = 1 / np.mean(np.diff(timestamps))
    
    # Calcola la trasformata di Fourier
    n = len(timestamps)
    fft_values = np.fft.fft(df.values)
    fft_freq = np.fft.fftfreq(n, d=1/fs)
    
    # Trova i picchi nella trasformata di Fourier
    peaks = np.where(np.abs(fft_values) > np.max(np.abs(fft_values)) * 0.1)[0]
    
    # Visualizza il grafico della trasformata di Fourier
    plt.figure(figsize=(10, 6))
    plt.plot(fft_freq, np.abs(fft_values))
    plt.title('Analisi di Fourier dei messaggi')
    plt.xlabel('Frequenza (Hz)')
    plt.ylabel('Ampiezza')
    plt.show()

    print(f"Frequenza campionaria: {fs} Hz")
    print(f"Picchi rilevati nelle frequenze: {fft_freq[peaks]} Hz")
