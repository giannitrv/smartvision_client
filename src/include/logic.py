import math
import json
import ipaddress
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage
from include.udpclient import UdpClient
from include.protocol import Protocol
from include.discovery import UDPDiscovery
from include.videoworker import VideoWorker

DEFAULT_ZOOM = 1.0
DEFAULT_PAN = 90
DEFAULT_TILT = 90

class MultivisionBackend(QObject):
    frame_ready = pyqtSignal(QImage)
    zoom_changed = pyqtSignal(float)
    auto_zoom_changed = pyqtSignal(bool)
    osd_enabled_changed = pyqtSignal(bool)
    connection_lost = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self._source_ip = 0
        self._source_port = 0
        self._cmd_port = 0
        self._zoom_factor = DEFAULT_ZOOM
        self._pan = DEFAULT_PAN
        self._tilt = DEFAULT_TILT
        self._auto_zoom = False
        self._enable_osd = False
        
        # Initialize discovery client
        self.discovery_client = UDPDiscovery(self)
        self.discovery_client.data_received.connect(self._on_discovery_data_received)
        
        self.udp_client = None
        self.video_worker = None

    def start_stream(self):
        if self.video_worker and not self.video_worker.isRunning():
            self.video_worker.start()

    def pause_stream(self):
        if self.video_worker:
            self.video_worker.stop()

    def get_current_zoom(self):
        return self._zoom_factor
        
    def _on_discovery_data_received(self, datagram):
        msg = json.loads(datagram.data().data())
        adr = int(ipaddress.IPv4Address(msg['ip']))
        
        # Robustness check: update if IP changed OR ports changed
        config_changed = (adr != self._source_ip) or \
                         (msg['rtsp'] != self._source_port) or \
                         (msg['cmd'] != self._cmd_port)
                         
        # Recreate worker if it has stopped (e.g., connection was lost)
        worker_dead = self.video_worker is None or not self.video_worker.isRunning()
                         
        if msg['device'] == 'multivision_system' and (config_changed or worker_dead):
            self._source_ip = adr
            self._source_port = msg['rtsp']
            self._cmd_port = msg['cmd']
            
            # Setup UDP Client only if configuration changed or it doesn't exist
            if config_changed or self.udp_client is None:
                self.udp_client = UdpClient(self._source_ip, self._cmd_port, 5005)
                self.udp_client.data_received.connect(self._on_data_received)
            
            # Cleanup old worker if exists
            if self.video_worker:
                self.video_worker.stop()
                self.video_worker.deleteLater()
            
            # Start new video worker
            url = f'rtsp://{msg["ip"]}:{self._source_port}/video'
            self.video_worker = VideoWorker(url)
            self.video_worker.frame_ready.connect(self.frame_ready)
            self.video_worker.connection_lost.connect(self.connection_lost)
            self.video_worker.start()

            # Send out of bounds values only to trigger the ack messages
            self._send_zoom(0.0)
            self._send_angles(255, 255)

    def _on_data_received(self, data):
        msg = json.loads(data.data())
        self._zoom_factor = msg['zoom']
        self._pan = msg['pan']
        self._tilt = msg['tilt']
        self._auto_zoom = msg['autoZoom']
        self._osd_enabled = msg['osdEnabled']
        self.zoom_changed.emit(self._zoom_factor)
        self.auto_zoom_changed.emit(self._auto_zoom)
        self.osd_enabled_changed.emit(self._osd_enabled)

    def increase_zoom(self):
        if self._zoom_factor < 5.0:
            self._zoom_factor += 0.5
            self._send_zoom(self._zoom_factor)

    def decrease_zoom(self):
        if self._zoom_factor > 1.0:
            self._zoom_factor -= 0.5
            self._send_zoom(self._zoom_factor)

    def set_zoom(self, value):
        new_zoom = value * 0.5
        if abs(new_zoom - self._zoom_factor) > 0.01: # simple debounce/check
            self._zoom_factor = new_zoom
            self.zoom_changed.emit(self._zoom_factor)
            self._send_zoom(self._zoom_factor)

    def move_up(self):
        self._tilt = 43
        self._send_angles(self._pan, self._tilt)

    def move_down(self):
        self._tilt = 45
        self._send_angles(self._pan, self._tilt)

    def move_left(self):
        self._pan = 43
        self._send_angles(self._pan, self._tilt)

    def move_right(self):
        self._pan = 45
        self._send_angles(self._pan, self._tilt)

    def move_reset(self):
        self._send_angles(self._pan, self._tilt, 1)

    def set_auto_zoom(self, autoZoom):
        if self.udp_client:
            message = Protocol.create_tracking_mode_cmd(autoZoom)
            self.udp_client.send_message(message)

    def take_picture(self):
        if self.udp_client:
            message = Protocol.create_camera_control_cmd(1, self._enable_osd)
            self.udp_client.send_message(message)

    def take_video(self):
        if self.udp_client:
            message = Protocol.create_camera_control_cmd(2, self._enable_osd)
            self.udp_client.send_message(message)

    def set_enable_osd(self, enable_osd):
        if self.udp_client:
            self._enable_osd = enable_osd
            message = Protocol.create_camera_control_cmd(0, self._enable_osd)
            self.udp_client.send_message(message)

    def _send_zoom(self, zoom):
        (f, i) = math.modf(zoom)
        if self.udp_client:
            message = Protocol.create_set_zoom_cmd(int(i), int(f*10))
            self.udp_client.send_message(message)

    def _send_angles(self, pan, tilt, reset=0):
        if self.udp_client:
            message = Protocol.create_set_angles_cmd(pan, tilt, reset)
            self.udp_client.send_message(message)

    def _parse_set_zoom_ack(self, data):
        self._zoom_factor = data[1] + data[2] / 10
        self.zoom_changed.emit(self._zoom_factor)

    def _parse_set_angles_ack(self, data):
        self._pan = data[1]
        self._tilt = data[2]

    def send_selection_area(self, x, y, w, h, frame_width, frame_height):
        print(f"Creating select area command: {x}, {y}, {w}, {h}")
        if self.udp_client and frame_width > 0 and frame_height > 0:
            # Normalize to 0-255
            norm_x = int((x / frame_width) * 255)
            norm_y = int((y / frame_height) * 255)
            norm_w = int((w / frame_width) * 255)
            norm_h = int((h / frame_height) * 255)
            # Ensure values are within byte range
            norm_x = max(0, min(255, norm_x))
            norm_y = max(0, min(255, norm_y))
            norm_w = max(0, min(255, norm_w))
            norm_h = max(0, min(255, norm_h))

            message = Protocol.create_target_tracking_cmd(norm_x, norm_y, norm_w, norm_h)
            self.udp_client.send_message(message)
