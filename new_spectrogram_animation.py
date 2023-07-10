import sounddevice as sd
import librosa
import numpy as np
import matplotlib.pyplot as plt

# Задаем параметры записи звука
duration = 0.7  # Длительность записи в секундах
sample_rate = 44100  # Частота дискретизации

fig, ax = plt.subplots(figsize=(10, 4))
spectrogram = None
num_of_spectrograms = 0
num_of_col = 0

def calculate_num_of_col(spectrogram):
    global num_of_col
    num_of_col = spectrogram.shape[1]
    print(num_of_col)

def update_spectrogram(frame):
    global spectrogram
    global num_of_spectrograms

    num_of_spectrograms += 1
    print(num_of_spectrograms)

    # Записываем звук с микрофона
    print("Запись начата. Говорите...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
    sd.wait()

    # Извлекаем спектрограмму из записанного звука
    audio = audio.flatten()
    new_spectrogram = np.array(librosa.amplitude_to_db(librosa.stft(audio), ref=np.max(audio)))

    if spectrogram is None:
        spectrogram = new_spectrogram
        calculate_num_of_col(spectrogram)
    else:
        if spectrogram.shape[1] > num_of_col * 3:
            spectrogram = np.delete(spectrogram, range(num_of_col), axis=1)
        spectrogram = np.concatenate((spectrogram, new_spectrogram), axis=1)
        print(spectrogram.shape[1])

    # Отображаем текущую спектрограмму
    ax.imshow(spectrogram, aspect='auto', origin='lower', cmap='inferno')
    ax.set_title('Спектрограмма')
    plt.draw()

# Запускаем обновление спектрограммы в цикле
while True:
    update_spectrogram(None)
    plt.pause(1)
