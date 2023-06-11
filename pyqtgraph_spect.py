import pyaudio
import numpy as np
import pyqtgraph as pg
from scipy import signal

CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
NUM_COLUMNS = 64
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

win = pg.GraphicsWindow()
plt = win.addPlot()
img = pg.ImageItem()

frequencies, times, spectrogram_data = signal.spectrogram(np.zeros(CHUNK), fs=RATE, window='hann', nperseg=2048, noverlap=1024)
img.setImage(spectrogram_data[:int(MAX_FREQUENCY)].T, autoLevels=True, levels=(VMIN, VMAX))
plt.addItem(img)

def update_spectrogram():
    # Чтение аудиоданных из потока
    data = stream.read(CHUNK)

    # Преобразование байтовых данных в числовой массив
    audio = np.frombuffer(data, dtype=np.int16)

    # Расчет спектрограммы
    _, _, spectrogram_data = signal.spectrogram(audio, fs=RATE, window='hann', nperseg=2048, noverlap=1024)
    img.setImage(spectrogram_data[:int(MAX_FREQUENCY)].T, autoLevels=True, levels=(VMIN, VMAX))

timer = pg.QtCore.QTimer()
timer.timeout.connect(update_spectrogram)
timer.start(0)

pg.QtGui.QApplication.exec_()

stream.stop_stream()
stream.close()
p.terminate()
