import pyaudio
import struct
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from matplotlib.animation import FuncAnimation


CHUNK = 1024 * 3
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
NUM_COLUMNS = 64  # Количество столбцов в спектрограмме
COLUMN_WIDTH = 1  # Ширина столбца в секундах
MAX_FREQUENCY = 22000  # Верхняя граница отображаемой частоты
VMIN = -50  # Минимальное значение амплитуды для цветовой шкалы
VMAX = 3  # Максимальное значение амплитуды для цветовой шкалы

p = pyaudio.PyAudio()

stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK
)

# Создание фигуры и осей для спектрограммы
fig, ax = plt.subplots(facecolor='white')

# Создание пустой спектрограммы
frequencies, times, spectrogram_data = signal.spectrogram(np.zeros(CHUNK), fs=RATE, window='hann', nperseg=2048, noverlap=1024)

# Создание пустой спектрограммы
spectrogram = ax.imshow(spectrogram_data[:int(MAX_FREQUENCY)], aspect='auto', origin='lower',
                        extent=[times[0], times[-1], frequencies[0], frequencies[-1]], vmax=VMAX, vmin=VMIN)

# Установка меток осей
plt.xlabel("Время (секунды)")
plt.ylabel("Частота (Гц)")
plt.title("Спектрограмма")
plt.colorbar(spectrogram, label="Амплитуда")

# Пустой массив для хранения столбцов спектрограммы
columns = np.zeros((spectrogram_data.shape[0], NUM_COLUMNS))


# Функция для инициализации анимации
def init():
    fig.patch.set_facecolor('white')
    return [spectrogram, fig.patch]

# Функция для обновления спектрограммы
def update_spectrogram(frame):

    # Чтение аудиоданных из потока
    data = stream.read(CHUNK)

    # Преобразование байтовых данных в числовой массив
    audio = np.frombuffer(data, dtype=np.int16)

    # Расчет спектрограммы
    _, _, spectrogram_data = signal.spectrogram(audio, fs=RATE, window='hann', nperseg=2048, noverlap=1024)

    y = 700000
    db = 20 * np.log10(spectrogram_data / y)

    print(np.max(db))
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

# Создание анимации
animation = FuncAnimation(fig, update_spectrogram, init_func=init, frames=None, interval=0, blit=True)

# Отображение спектрограммы
plt.show()

# Остановка потока и освобождение ресурсов
stream.stop_stream()
stream.close()
p.terminate()
