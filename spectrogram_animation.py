import time

import pyaudio
import struct
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from matplotlib.animation import FuncAnimation
import tkinter as tk
from matplotlib.widgets import Slider
import matplotlib.colors as colors
import tkinter as tk
from time import sleep



CHUNK = 1024 * 3
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
NUM_COLUMNS = 60
MAX_FREQUENCY = 22000
VMIN = -100
VMAX = 30
NOISE_THRESHOLD = -40  # Пороговое значение для шума


target_frequency = 50
tolerance = 20
times = (0.04643991, 0.02321995)


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
ax_slider = plt.axes([0.2, 0.03, 0.6, 0.03])  # Позиция ползунка на окне
brightness_slider = Slider(ax_slider, 'Нижний порог', -100, -30, valinit=VMIN)  # Создание ползунка




frequencies, _, spectrogram_data = signal.spectrogram(np.zeros(CHUNK), fs=RATE, window='hann', nperseg=2048, noverlap=1024)
spectrogram = ax.imshow(spectrogram_data[:int(MAX_FREQUENCY)], aspect='auto', origin='lower',
                        extent=[times[0], times[-1], frequencies[0], frequencies[-1]], vmax=VMAX, vmin=VMIN)


plt.xlabel("Время (секунды)")
plt.ylabel("Частота (Гц)")
plt.colorbar(spectrogram, label="Амплитуда")

columns = np.zeros((spectrogram_data.shape[0], NUM_COLUMNS))

rec_dur = 0
j = 0
hist_db = []

def nearest(lst, target):
  nearest_value = min(lst, key=lambda x: abs(x-target))
  return lst.index(nearest_value)

# Создание окна
window = tk.Tk()
pause = False
# Функция, вызываемая при нажатии кнопки "Анализировать"
def analyze_button_click():
    global pause
    h = 20
    pause ^= True
    rect_width = (times[0] - times[1]) / NUM_COLUMNS # Ширина квадрата (длительность временного сегмента)
    rect_x = times[0]
    rect_y = 0
    print(rect_width)
    # rect_height = hist_db[0][0][1] - hist_db[0][0][0] # Высота квадрата (диапазон частоты)
    rect_height = 1000
    if pause:
        rects = []
        for i, col in enumerate(hist_db[-NUM_COLUMNS:]):
            rect_x -= rect_width
            rect_y = 0
            # rect_height = 0
            amps = []
            for lst in col:
                amps.append(np.average(lst))
            np_amps = np.array(amps)
            noise_freqs = np.where(np_amps < -180)
            for noise_freq in noise_freqs:
                if np.array_equal(noise_freq, np.arange(0, 1025)):
                    rect_xy = (rect_x, rect_y)
                    rect_height = 20000
                    rect = plt.Rectangle(rect_xy, rect_width, rect_height, facecolor='blue', alpha=0.5)
                    rects.append(rect)
                    ax.add_patch(rect)
                    # plt.pause(0.001)
                else:
                    flag = False
                    for i, freq in enumerate(noise_freq):
                        if i % h == 0:
                            if freq - noise_freq[i - h] == h:
                                rect_height += 20000 / len(noise_freq) * h
                                if not flag:
                                    rect_y = frequencies[freq]
                                    flag = True
                            else:
                                if flag:
                                    print('im here')
                                    rect_xy = (rect_x, rect_y)
                                    rect = plt.Rectangle(rect_xy, rect_width, rect_height, facecolor='blue', alpha=0.5)
                                    rects.append(rect)
                                    ax.add_patch(rect)
                                    flag = False
                                else:
                                    rect_y = frequencies[freq]
                                    rect_xy = (rect_x, rect_y)
                                    rect_height = 20000 / len(noise_freq) * 20
                                    rect = plt.Rectangle(rect_xy, rect_width, rect_height, facecolor='blue', alpha=0.5)
                                    rects.append(rect)
                                    ax.add_patch(rect)
                                    flag = False

                    plt.pause(0.003)

            # print(np.arange(1, 1025))
            # for noise_freq in noise_freqs:
                # if noise_freq != np.arange(1, 1025):
                #     print('yooooo')
            # rect_y += rect_height
            #
            # rect_xy = (rect_x, rect_y)
            # rect = plt.Rectangle(rect_xy, rect_width, rect_height, facecolor='blue', alpha=0.5)
            # rects.append(rect)
            # ax.add_patch(rect)
            # plt.pause(0.001)

# Создание кнопки
analyze_button = tk.Button(window, text="Анализировать", command=analyze_button_click)

# Размещение кнопки на окне
analyze_button.pack()

def update_brightness(val):
    brightness = brightness_slider.val  # Получение текущего значения яркости
    spectrogram.set_clim(vmin=brightness)  # Изменение яркости спектрограммы
    fig.canvas.draw_idle()  # Обновление окна

brightness_slider.on_changed(update_brightness)

def update_spectrogram(a):
    while not pause:
        fig.set_facecolor('white')
        global rect_x, rect
        global rects
        global rec_dur
        global j
        j += 1

        # Чтение аудиоданных из потока
        data = stream.read(CHUNK)

        # Преобразование байтовых данных в числовой массив
        audio = np.frombuffer(data, dtype=np.int16)

        # Расчет спектрограммы
        frequencies, _, spectrogram_data = signal.spectrogram(audio, fs=RATE, window='hann', nperseg=2048, noverlap=1024)
        rec_dur += times[1] - times[0]
        # print(frequencies)

        y = 1000000
        db = np.array(20 * np.log10(abs(spectrogram_data) / y))
        hist_db.append(db)
        # print(len(db))
        if -10 <= np.max(db) <= 0:
            fig.set_facecolor('yellow')
        if np.max(db) >= 0:
            fig.set_facecolor('red')
        print(len(hist_db))
        # Перевод амплитуды в дБ
        spectrogram_data = 20 * np.log10(spectrogram_data/100)

        # Настройка цветовой карты для выделения шумов
        spectrogram.set_cmap('inferno')  # Используйте любую цветовую карту, которая подходит вам

        columns[:, :-1] = columns[:, 1:]
        columns[:, -1] = spectrogram_data[:int(MAX_FREQUENCY), 0]
        # Обновление спектрограммы
        spectrogram.set_array(columns)



        return (spectrogram)


def animate_spectrogram():
    animation = FuncAnimation(fig, update_spectrogram, frames=None, interval=0, blit=False)
    plt.show()

def stop_stream():
    stream.stop_stream()
    stream.close()
    p.terminate()

# Start the animation
animate_spectrogram()



# Запуск главного цикла обработки событий окна
window.mainloop()