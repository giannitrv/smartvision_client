import sys
import os
import math
import cv2
import time
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QGroupBox
from PyQt5.QtGui import QImage, QPixmap, QIcon
from PyQt5.QtCore import QTimer, Qt, QSize
from include.udpclient import UdpClient
from include.protocol import Protocol

class VideoStream(QWidget):
    def __init__(self):
        super().__init__()
        self._source_ip = (os.getenv('SOURCE_IP'))
        self._source_port = (os.getenv('RTSP_PORT'))
        self._udp_port = (os.getenv('UDP_PORT'))

        self._zoom_factor = 1.0
        self._pan = 100
        self._tilt = 80

        # Initialize UDP Client
        client_port = 12346
        self.udp_client = UdpClient(self._source_ip, self._udp_port, client_port)
        self.udp_client.data_received.connect(self._on_data_received)
        # Layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        zoom_layout = QVBoxLayout()
        move_layout = QGridLayout()
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
        up_button = QPushButton()
        up_button.setIcon(QIcon('src/up_arrow.png'))
        up_button.setIconSize(QSize(24, 24))
        up_button.setFixedSize(30, 30)
        down_button = QPushButton()
        down_button.setIcon(QIcon('src/down_arrow.png'))
        down_button.setIconSize(QSize(24, 24))
        down_button.setFixedSize(30, 30)
        left_button = QPushButton()
        left_button.setIcon(QIcon('src/left_arrow.png'))
        left_button.setIconSize(QSize(24, 24))
        left_button.setFixedSize(30, 30)
        right_button = QPushButton()
        right_button.setIcon(QIcon('src/right_arrow.png'))
        right_button.setIconSize(QSize(24, 24))
        right_button.setFixedSize(30, 30)
        reset_button = QPushButton('Reset')
        picture_button = QPushButton("Picture")
        video_button = QPushButton("Video")
        zoom_gb = QGroupBox("Zoom")
        move_gb = QGroupBox("Move")
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

        right_layout.addWidget(move_gb)
        move_gb.setLayout(move_layout)
        move_layout.addWidget(up_button, 0, 1)
        move_layout.addWidget(down_button, 2, 1)
        move_layout.addWidget(left_button, 1, 0)
        move_layout.addWidget(right_button, 1, 2)
        move_layout.addWidget(reset_button, 3, 0, 1, 3)
        right_layout.addWidget(control_gb)
        control_gb.setLayout(control_layout)
        control_layout.addWidget(picture_button)
        control_layout.addWidget(video_button)
        right_layout.addStretch()

        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(right_layout)
        # Set main layout
        self.setLayout(main_layout)
        # Capture RTSP stream
        self.cap = cv2.VideoCapture(f'rtsp://{self._source_ip}:{self._source_port}/video', cv2.CAP_FFMPEG)
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
        up_button.setAutoRepeatInterval(200)
        down_button.clicked.connect(self._move_down)
        down_button.setAutoRepeat(True)
        down_button.setAutoRepeatDelay(100)
        down_button.setAutoRepeatInterval(200)
        left_button.clicked.connect(self._move_left)
        left_button.setAutoRepeat(True)
        left_button.setAutoRepeatDelay(100)
        left_button.setAutoRepeatInterval(200)
        right_button.clicked.connect(self._move_right)
        right_button.setAutoRepeat(True)
        right_button.setAutoRepeatDelay(100)
        right_button.setAutoRepeatInterval(200)
        reset_button.clicked.connect(self._move_reset)

        # Start stream
        self.start_stream()

    def _on_data_received(self, data):
        print(data)

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
            time.sleep(0.5)
            self.cap = cv2.VideoCapture(f'rtsp://{self._source_ip}:{self._source_port}/video', cv2.CAP_FFMPEG)
            if not self.cap.isOpened():
                pixmap = QPixmap("video_error.jpg")
                self.video_label.setPixmap(pixmap)

    def _increase_zoom(self):
        if self._zoom_factor < 5.0:
            self._zoom_factor += 0.5
            self.slider.setValue(int(self._zoom_factor*2))
            self._update_label()
            self._send_zoom()

    def _decreasse_zoom(self):
        if self._zoom_factor > 1.0:
            self._zoom_factor -= 0.5
            self.slider.setValue(int(self._zoom_factor*2))
            self._update_label()
            self._send_zoom()

    def _update_zoom(self):
        self._zoom_factor = self.slider.value()*0.5
        self._update_label()

    def _move_up(self):
        if self._tilt < 180:
            self._tilt += 5
            self._send_angles()

    def _move_down(self):
        if self._tilt > 0:
            self._tilt -= 5
            self._send_angles()

    def _move_left(self):
        if self._pan < 180:
            self._pan += 5
            self._send_angles()

    def _move_right(self):
        if self._pan > 0:
            self._pan -= 5
            self._send_angles()   

    def _move_reset(self):
        self._pan = 100
        self._tilt = 80
        self._send_angles()

    def _update_label(self):
        self.zoom_label.setText(str(self._zoom_factor))

    def _send_zoom(self):
        (f, i) = math.modf(self._zoom_factor)
        message = Protocol.create_setzoom_cmd(int(i), int(f*10))
        self.udp_client.send_message(message)

    def _send_angles(self):
        message = Protocol.create_setangles_cmd(self._pan, self._tilt)
        self.udp_client.send_message(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("MultiVision Client")
    stream = VideoStream()
    stream.show()
    sys.exit(app.exec_())

