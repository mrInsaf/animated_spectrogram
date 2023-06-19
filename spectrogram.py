import pyaudio
import numpy as np

CHUNK = 1024  # Размер буфера аудио
RATE = 44100  # Частота дискретизации
TARGET_FREQUENCY = 50  # Целевая частота сетевого шума
TOLERANCE = 20  # Допустимое отклонение от целевой частоты

p = pyaudio.PyAudio()

stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

while True:
    # Чтение аудио из потока
    data = stream.read(CHUNK)
    audio = np.frombuffer(data, dtype=np.int16)

    # Применение быстрого преобразования Фурье (FFT)
    spectrum = np.fft.fft(audio)

    harmonics = [1, 2, 3, 4, 5]  # Список гармоник для проверки

    for harmonic in harmonics:
        harmonic_frequency = TARGET_FREQUENCY * harmonic
        harmonic_index = int(harmonic_frequency * CHUNK / RATE)
        harmonic_amplitude = np.abs(spectrum[harmonic_index])

        if harmonic_amplitude > np.mean(np.abs(spectrum)) * TOLERANCE:
            print(f"Обнаружена гармоника {harmonic_frequency} Гц!")

stream.stop_stream()
stream.close()
p.terminate()
