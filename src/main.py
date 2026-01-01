import sys
import os
import math
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QWidget, QGroupBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtNetwork import QUdpSocket, QHostAddress
from PyQt5.QtCore import QTimer, Qt, QByteArray
from protocol import Protocol

class VideoStream(QWidget):
    def __init__(self):
        super().__init__()
        self._source_ip = (os.getenv('SOURCE_IP'))
        self._source_port = (os.getenv('RTSP_PORT'))
        self._udp_port = (os.getenv('UDP_PORT'))
        self.sock = QUdpSocket()
        self._zoom_factor = 1.0
        self._pitch = 100
        # Impostiamo la porta di ricezione del client
        self.client_port = 12346  # Porta su cui il client riceve risposte
        self.sock.bind(QHostAddress.Any, self.client_port)
        # Layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        zoom_layout = QVBoxLayout()
        move_layout = QVBoxLayout()
        control_layout = QVBoxLayout()
        # Widgets
        self.video_label = QLabel()
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(2)
        self.slider.setMaximum(10)
        self.slider.setSingleStep(1)
        play_button = QPushButton('Play')
        pause_button = QPushButton('Pause')
        self.zoom_label = QLabel(str(self._zoom_factor))
        zoom_in_button = QPushButton('+')
        zoom_out_button = QPushButton('-')
        up_button = QPushButton('Move up')
        down_button = QPushButton('Move down')
        left_button = QPushButton('Move left')
        right_button = QPushButton('Move right')
        picture_putton = QPushButton("Picture")
        video_putton = QPushButton("Video")
        zoom_gb = QGroupBox("Zoom")
        angle_gb = QGroupBox("Angles")
        control_gb = QGroupBox("Control")
        # Add widget to layout
        left_layout.addWidget(play_button)
        left_layout.addWidget(pause_button)
        left_layout.addWidget(zoom_gb)
        zoom_gb.setLayout(zoom_layout)
        zoom_layout.addWidget(zoom_in_button)
        zoom_layout.addWidget(self.slider)
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(zoom_out_button)
        zoom_layout.setAlignment(self.slider, Qt.AlignHCenter)
        zoom_layout.setAlignment(self.zoom_label, Qt.AlignHCenter)
        left_layout.addStretch()

        right_layout.addWidget(angle_gb)
        angle_gb.setLayout(move_layout)
        move_layout.addWidget(up_button)
        move_layout.addWidget(down_button)
        move_layout.addWidget(left_button)
        move_layout.addWidget(right_button)
        right_layout.addWidget(control_gb)
        control_gb.setLayout(control_layout)
        control_layout.addWidget(picture_putton)
        control_layout.addWidget(video_putton)
        right_layout.addStretch()

        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(right_layout)
        # Set main layout
        self.setLayout(main_layout)
        # Capture RTSP stream
        self.cap = cv2.VideoCapture(f'rtsp://{self._source_ip}:{self._source_port}/mystream')
        # Timer for frame update
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)
        # Functions binding
        play_button.clicked.connect(self.start_stream)
        pause_button.clicked.connect(self.pause_stream)
        zoom_in_button.clicked.connect(self._increase_zoom)
        zoom_out_button.clicked.connect(self._decreasse_zoom)
        self.slider.sliderReleased.connect(self._send_zoom)
        self.slider.valueChanged.connect(self._update_zoom)
        up_button.clicked.connect(self._move_up)
        up_button.setAutoRepeat(True)
        up_button.setAutoRepeatDelay(100)
        up_button.setAutoRepeatInterval(1000)

        self.sock.readyRead.connect(self.readPendingDatagrams)
        # Start stream
        self.start_stream()

    def readPendingDatagrams(self):
        while self.sock.hasPendingDatagrams():
            datagram_size = self.sock.pendingDatagramSize()
            datagram = self.sock.receiveDatagram(datagram_size)
            print(datagram.data())

    def start_stream(self):
        self.timer.start(16)

    def pause_stream(self):
        self.timer.stop()

    def _update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
        else:
            pixmap = QPixmap("video_error.jpg")
            self.video_label.setPixmap(pixmap)

    def _increase_zoom(self):
        if self._zoom_factor < 5.0:
            self._zoom_factor += 0.5
            self.slider.setValue(int(self._zoom_factor * 2))
            self._update_label()
            self._send_zoom()

    def _decreasse_zoom(self):
        if self._zoom_factor > 1.0:
            self._zoom_factor -= 0.5
            self.slider.setValue(int(self._zoom_factor * 2))
            self._update_label()
            self._send_zoom()

    def _update_zoom(self):
        self._zoom_factor = self.slider.value()*0.5
        self._update_label()

    def _move_up(self):
        pass

    def _move_down(self):
        pass

    def _move_left(self):
        pass

    def _move_right(self):
        pass

    def _update_label(self):
        self.zoom_label.setText(str(self._zoom_factor))

    def _send_zoom(self):
        (f, i) = math.modf(self._zoom_factor)
        message = Protocol.create_setzoom_cmd(int(i), int(f*10))
        self.sock.writeDatagram(message, QHostAddress(self._source_ip), int(self._udp_port))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("MultiVision Client")
    stream = VideoStream()
    stream.show()
    sys.exit(app.exec_())

