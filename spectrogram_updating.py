import time
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Slider
import tkinter as tk

CHUNK = 1024 * 3
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 10000
NUM_COLUMNS = 30
MAX_FREQUENCY = 1025
VMIN = -100
VMAX = 0
NOISE_THRESHOLD = -300  # Пороговое значение для шума

target_frequency = 50
tolerance = 20
times = (0.04643991, 0.02321995)

nperseg = int(CHUNK / 2)
noverlap = nperseg / 2

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
ax_brightness_slider = plt.axes([0.2, 0.03, 0.6, 0.03])  # Позиция ползунка на окне
brightness_slider = Slider(ax_brightness_slider, 'Нижний порог', -100, -30, valinit=VMIN)  # Создание ползунка

ax_sense_slider = plt.axes([0.2, 0.06, 0.6, 0.03])  # Позиция ползунка на окне
sense_slider = Slider(ax_sense_slider, 'Нижний порог', -200, -30, valinit=NOISE_THRESHOLD)  # Создание ползунка

frequencies, _, spectrogram_data = signal.spectrogram(np.zeros(CHUNK), fs=RATE, window='hann', nperseg=nperseg,
                                                      noverlap=noverlap)
spectrogram = ax.imshow(spectrogram_data[:int(MAX_FREQUENCY)], aspect='auto', origin='lower',
                        extent=[times[0], times[-1], frequencies[0], frequencies[-1]], vmax=VMAX, vmin=VMIN)
# Настройка цветовой карты
spectrogram.set_cmap('inferno')  # Используйте любую цветовую карту, которая подходит вам

plt.xlabel("Время (секунды)")
plt.ylabel("Частота (Гц)")
plt.colorbar(spectrogram, label="Амплитуда")

columns = np.zeros((spectrogram_data.shape[0], NUM_COLUMNS))

rec_dur = 0
j = 0
hist_db = []
rects = []
rect_width = (times[0] - times[1]) / NUM_COLUMNS
rect_height = (rect_width * 20 ** 4) * RATE / 10000
max_rects = int((RATE/2) / rect_height)
rect_x = times[0]

# Создание окна
window = tk.Tk()
pause = False


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]


def detect_50hz_anomaly():
    global pause, rects
    h = 10
    pause ^= True
    pass

# Создание кнопки
fifty_hz_button = tk.Button(window, text="Выявить помехи 50гц", command=detect_50hz_anomaly)

# Размещение кнопки на окне
fifty_hz_button.pack()



def update_brightness(val):
    brightness = brightness_slider.val  # Получение текущего значения яркости
    spectrogram.set_clim(vmin=brightness)  # Изменение яркости спектрограммы
    fig.canvas.draw_idle()  # Обновление окна

brightness_slider.on_changed(update_brightness)

def update_sensetivity(val):
    global NOISE_THRESHOLD
    sense = sense_slider.val
    NOISE_THRESHOLD = sense
    fig.canvas.draw_idle()  # Обновление окна

sense_slider.on_changed(update_sensetivity)


def toggle_button_color():
    global fifty_hz_button
    fifty_hz_button.config(bg="red")


def build_spectrogram():
    # Чтение аудиоданных из потока
    data = stream.read(CHUNK)

    # Преобразование байтовых данных в числовой массив
    audio = np.frombuffer(data, dtype=np.int16)

    # Расчет спектрограммы
    _, _, spectrogram_data = signal.spectrogram(audio, fs=RATE, window='hann', nperseg=nperseg, noverlap=noverlap)
    # Перевод амплитуды в дБ
    y = np.max(spectrogram_data)
    amplitudes = 20 * np.log10(spectrogram_data / y)
    return spectrogram_data, amplitudes


def amps_to_db(spectrogram_data):
    y = 10 ** 6
    db = np.array(20 * np.log10(abs(spectrogram_data) / y))
    hist_db.append(db)
    return db


def detect_peak(db):
    if -10 <= np.max(db) <= 0:
        fig.set_facecolor('yellow')
    if np.max(db) >= 0:
        fig.set_facecolor('red')

def detect_harmonics(db, base_frequency):
    fifty_hz_button.config(bg="white")
    threshold = -120
    bf = base_frequency
    num_harmonics = 10
    amps = []
    harmonics_idx = []
    try:
        for i, point in enumerate(db):
            amps.append(np.average(point))
        for harmonic in range(1, num_harmonics):
            freq = find_nearest(frequencies, bf * harmonic)
            freq_idx = np.where(frequencies == freq)[0][0]
            if amps[freq_idx] > threshold:
                harmonics_idx.append(freq_idx)
                toggle_button_color()
        return harmonics_idx
    except Exception as ex:
        print(ex)
        pass

def create_rect(idx, rect_type):
    if rect_type == 'noise':
        rect = plt.Rectangle((0.02327 - rect_width, frequencies[idx]), rect_width, rect_height, edgecolor='blue',
                             fill=False)
        rects.append(rect)
        ax.add_patch(rect)
    elif rect_type == 'harmonic':
        rect = plt.Rectangle((0.02327 - rect_width, frequencies[idx]), rect_width / 4, rect_height / 4, edgecolor='purple',
                             fill=False)
        rects.append(rect)
        ax.add_patch(rect)


def create_new_squares(db):
    noise_idx = np.where(db < NOISE_THRESHOLD)
    noise_idx = np.unique(noise_idx)
    harmoics_idx = detect_harmonics(db, 300)
    if len(noise_idx) >= max_rects:
        step = int(len(noise_idx) / max_rects)
    else:
        step = len(db)
    noise_idx = noise_idx[::step]
    # harmoics_idx = harmoics_idx[::step]
    if len(rects) == 0:
        create_rect(0, 'noise')
    for idx in harmoics_idx:
        create_rect(idx, 'harmonic')
    for idx in noise_idx:
        if np.abs(frequencies[idx] - rects[-1].get_y()) > rect_height:
            create_rect(idx, 'noise')





def clear_patches(rects):
    if len(rects) > 0:
        if rects[0].get_x() > rect_x:
            for rect in rects:
                if rect.get_x() > rect_x:
                    rects.remove(rect)
                else:
                    break

def update_squares():
    for rect in rects:
        current_x = rect.get_x()
        new_x = current_x + rect_width
        rect.set_x(new_x)

def update_spectrogram():
    while not pause:
        print(len(rects))
        if len(hist_db) <= NUM_COLUMNS:
            fig.set_facecolor('white')

            spectrogram_data, amplitudes = build_spectrogram()
            db = amps_to_db(spectrogram_data)
            detect_peak(db)

            if len(rects) < 400:
                create_new_squares(db)

            update_squares()

            clear_patches(rects)

            columns[:, :-1] = columns[:, 1:]
            columns[:, -1] = amplitudes[:int(MAX_FREQUENCY), 0]
            # Обновление спектрограммы
            spectrogram.set_array(columns)
            plt.pause(0.1)
        else:
            pass
            hist_db.pop(0)
            # plt.pause(0.1)


def stop_stream():
    stream.stop_stream()
    stream.close()
    p.terminate()


# Start the animation
update_spectrogram()
window.mainloop()
