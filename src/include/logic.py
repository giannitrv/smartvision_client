import math
import cv2
import json
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QImage
from include.udpclient import UdpClient
from include.protocol import Protocol
from include.discovery import UDPDiscovery

DEFAULT_ZOOM = 1.0
DEFAULT_PAN = 90
DEFAULT_TILT = 90

class MultivisionBackend(QObject):
    frame_ready = pyqtSignal(QImage)
    zoom_changed = pyqtSignal(float)
    connection_lost = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._source_ip = ""
        self._source_port = 0
        self._cmd_port = 0
        self._zoom_factor = DEFAULT_ZOOM
        self._pan = DEFAULT_PAN
        self._tilt = DEFAULT_TILT
        
        # Initialize discovery client
        self.discovery_client = UDPDiscovery(self)
        self.discovery_client.data_received.connect(self._on_discovery_data_received)
        
        self.udp_client = None
        
        # Capture RTSP stream
        self.cap = cv2.VideoCapture()
        
        # Timer for frame update
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_frame)

    def start_stream(self):
        self.timer.start(16)

    def pause_stream(self):
        self.timer.stop()

    def get_current_zoom(self):
        return self._zoom_factor
        
    def _on_discovery_data_received(self, datagram):
        msg = json.loads(datagram.data().data())
        adr = datagram.senderAddress().toIPv4Address()
        if msg['device'] == 'multivision_system':
            if adr != self._source_ip:
                self._source_ip = adr
                self._source_port = msg['rtsp']
                self._cmd_port = msg['cmd']
                self.udp_client = UdpClient(self._source_ip, self._cmd_port, 5005)
                self.udp_client.data_received.connect(self._on_data_received)
                self.cap.open(f'rtsp://{self._source_ip}:{self._source_port}/video', cv2.CAP_FFMPEG)
                if self.cap.isOpened():
                    self.start_stream()
                    # Send out of bounds values only to trigger the ack messages
                    self._send_zoom(0.0)
                    self._send_angles(255, 255)
                else:
                    self.connection_lost.emit()

    def _on_data_received(self, data):
        data = data.data()
        if data[0] == 0x01:
            self._parse_setzoom_ack(data)
        elif data[0] == 0x02:
            self._parse_setangles_ack(data)

    def _update_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_ready.emit(qt_image)
        else:
            self.connection_lost.emit()
            self.pause_stream()

    def increase_zoom(self):
        if self._zoom_factor < 5.0:
            self._zoom_factor += 0.5
            self.zoom_changed.emit(self._zoom_factor)
            self._send_zoom(self._zoom_factor)

    def decrease_zoom(self):
        if self._zoom_factor > 1.0:
            self._zoom_factor -= 0.5
            self.zoom_changed.emit(self._zoom_factor)
            self._send_zoom(self._zoom_factor)

    def set_zoom(self, value):
        # Assuming value comes from slider (int), need to convert back if logic requires float, 
        # or if the UI passes the raw slider value.
        # Looking at original main.py:
        # self._zoom_factor = self.slider.value()*0.5
        new_zoom = value * 0.5
        if abs(new_zoom - self._zoom_factor) > 0.01: # simple debounce/check
            self._zoom_factor = new_zoom
            self.zoom_changed.emit(self._zoom_factor)
            self._send_zoom(self._zoom_factor)

    def move_up(self):
        if self._tilt < 180:
            self._tilt += 5
            self._send_angles(self._pan, self._tilt)

    def move_down(self):
        if self._tilt > 0:
            self._tilt -= 5
            self._send_angles(self._pan, self._tilt)

    def move_left(self):
        if self._pan < 180:
            self._pan += 5
            self._send_angles(self._pan, self._tilt)

    def move_right(self):
        if self._pan > 0:
            self._pan -= 5
            self._send_angles(self._pan, self._tilt)

    def move_reset(self):
        self._pan = DEFAULT_PAN
        self._tilt = DEFAULT_TILT
        self._send_angles(self._pan, self._tilt)

    def take_picture(self):
        if self.udp_client:
            message = Protocol.create_cameracontrol_cmd(0)
            self.udp_client.send_message(message)

    def take_video(self):
        if self.udp_client:
            message = Protocol.create_cameracontrol_cmd(1)
            self.udp_client.send_message(message)

    def _send_zoom(self, zoom):
        (f, i) = math.modf(zoom)
        if self.udp_client:
            message = Protocol.create_setzoom_cmd(int(i), int(f*10))
            self.udp_client.send_message(message)

    def _send_angles(self, pan, tilt):
        if self.udp_client:
            message = Protocol.create_setangles_cmd(pan, tilt)
            self.udp_client.send_message(message)

    def _parse_setzoom_ack(self, data):
        self._zoom_factor = data[1] + data[2] / 10
        self.zoom_changed.emit(self._zoom_factor)

    def _parse_setangles_ack(self, data):
        self._pan = data[1]
        self._tilt = data[2]
