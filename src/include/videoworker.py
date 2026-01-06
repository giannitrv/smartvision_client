from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
import cv2

class VideoWorker(QThread):
    frame_ready = pyqtSignal(QImage)
    connection_lost = pyqtSignal()

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = False

    def run(self):
        self.running = True
        cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            self.connection_lost.emit()
            self.running = False
            return
            
        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                self.frame_ready.emit(qt_image)
            else:
                self.connection_lost.emit()
                break
        cap.release()

    def stop(self):
        self.running = False
        self.wait()