import pyaudio
import struct
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from matplotlib.animation import FuncAnimation
import ipywidgets

CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
NUM_COLUMNS = 64
COLUMN_WIDTH = 1
MAX_FREQUENCY = 22000
VMIN = -50
VMAX = 3

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

fig, ax = plt.subplots()

frequencies, times, spectrogram_data = signal.spectrogram(np.zeros(CHUNK), fs=RATE, window='hann', nperseg=2048, noverlap=1024)
spectrogram = ax.imshow(spectrogram_data[:int(MAX_FREQUENCY)], aspect='auto', origin='lower',
                        extent=[times[0], times[-1], frequencies[0], frequencies[-1]], vmax=VMAX, vmin=VMIN)


plt.xlabel("Время (секунды)")
plt.ylabel("Частота (Гц)")
plt.title("Спектрограмма")
plt.colorbar(spectrogram, label="Амплитуда")

columns = np.zeros((spectrogram_data.shape[0], NUM_COLUMNS))

def update_spectrogram(ax):



    # Чтение аудиоданных из потока
    data = stream.read(CHUNK)

    # Преобразование байтовых данных в числовой массив
    audio = np.frombuffer(data, dtype=np.int16)

    # Расчет спектрограммы
    _, _, spectrogram_data = signal.spectrogram(audio, fs=RATE, window='hann', nperseg=2048, noverlap=1024)

    y = 1500000
    db = 20 * np.log10(abs(spectrogram_data) / y)
    if -10 <= np.max(db) <= 0:
        print('Опасная зона!')
    elif np.max(db) >= 0:
        print('ПЕРЕГРУЗКА!!!')

    # Перевод амплитуды в дБ
    spectrogram_data = 20 * np.log10(spectrogram_data/100)

    # Обновление массива со столбцами спектрограммы
    columns[:, :-1] = columns[:, 1:]
    columns[:, -1] = spectrogram_data[:int(MAX_FREQUENCY), 0]

    # Обновление спектрограммы
    spectrogram.set_array(columns)

    return (spectrogram,)

def animate_spectrogram():
    animation = FuncAnimation(fig, update_spectrogram, frames=None, interval=0, blit=True)
    plt.show()

def stop_stream():
    stream.stop_stream()
    stream.close()
    p.terminate()
