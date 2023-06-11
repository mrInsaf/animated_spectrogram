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
NUM_COLUMNS = 80
COLUMN_WIDTH = 1
MAX_FREQUENCY = 22000
VMIN = -50
VMAX = 3

target_frequency = 50
tolerance = 20


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


# class HarmRect:
#     def __init__(self, init_rect_x=0.04, init_rect_y=0, rect_width = 0.001, rect_height = 500):
#         self.rect_x = init_rect_x  # Координата x (время) квадрата
#         self.rect_y = init_rect_y  # Начальная координата y (частота) квадрата
#         self.width = rect_width  # Ширина квадрата
#         self.height = rect_height  # Высота квадрата (диапазон частоты)
#
#     def show_info(self):
#         print('rect_x=', self.rect_x, ' rect_y=', self.rect_y, ' width=', self.width, ' height=', self.height)


rects = []


def update_spectrogram(a):
    fig.set_facecolor('white')
    global rect_x
    global rects

    # Чтение аудиоданных из потока
    data = stream.read(CHUNK)

    # Преобразование байтовых данных в числовой массив
    audio = np.frombuffer(data, dtype=np.int16)

    # Расчет спектрограммы
    frequencies, times, spectrogram_data = signal.spectrogram(audio, fs=RATE, window='hann', nperseg=2048, noverlap=1024)

    y = 1500000
    db = 20 * np.log10(abs(spectrogram_data) / y)
    if -10 <= np.max(db) <= 0:
        print('Опасная зона!')
        fig.set_facecolor('yellow')
    elif np.max(db) >= 0:
        print('ПЕРЕГРУЗКА!!!')
        fig.set_facecolor('red')

    # Перевод амплитуды в дБ
    spectrogram_data = 20 * np.log10(spectrogram_data/100)

    # Обновление массива со столбцами спектрограммы
    columns[:, :-1] = columns[:, 1:]
    columns[:, -1] = spectrogram_data[:int(MAX_FREQUENCY), 0]

    # Обновление спектрограммы
    spectrogram.set_array(columns)

    # Поиск областей с положительной громкостью
    positive_areas = np.where(spectrogram_data[:int(MAX_FREQUENCY), :] > 0)

    # Создание новых квадратов в местах скачков амплитуды
    for freq_idx, col_idx in zip(positive_areas[0], positive_areas[1]):
        if len(rects) > 4:
            break
        elif len(rects) == 0:
            rect_x = 0.05  # Координата x (время) квадрата
            rect_y = frequencies[freq_idx]  # Начальная координата y (частота) квадрата
            rect_width = -0.001  # Ширина квадрата
            rect_height = 200  # Высота квадрата (диапазон частоты)
            rect_xy = (rect_x, rect_y)

            rect = plt.Rectangle(rect_xy, rect_width, rect_height, facecolor='white', alpha=0.8)
            ax.add_patch(rect)
            rects.append(rect)
        elif len(rects) > 0:
            rect_x = 0.05  # Координата x (время) квадрата
            rect_y = frequencies[freq_idx]  # Начальная координата y (частота) квадрата
            rect_width = -0.001  # Ширина квадрата
            rect_height = 200  # Высота квадрата (диапазон частоты)
            rect_xy = (rect_x, rect_y)
            for rect in rects:
                if abs(rect_y - rect.get_x()) > 200:
                    rect = plt.Rectangle(rect_xy, rect_width, rect_height, facecolor='white', alpha=0.8)
                    ax.add_patch(rect)
                    rects.append(rect)

                    # print(len(rects))


    if len(rects) > 0:
        new_rects = []
        for rect in rects:
            if rect.get_x() > 0.023:
                rect.set_x(rect.get_x() - 0.023 / NUM_COLUMNS)
                print(rect.get_x())
                new_rects.append(rect)
        rects = new_rects


    return (spectrogram, *rects)

def animate_spectrogram():
    animation = FuncAnimation(fig, update_spectrogram, frames=None, interval=0, blit=False)
    plt.show()

def stop_stream():
    stream.stop_stream()
    stream.close()
    p.terminate()

# animate_spectrogram()
