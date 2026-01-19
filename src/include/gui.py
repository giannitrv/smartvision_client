from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QSlider, QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QGroupBox, QRubberBand
from PyQt5.QtGui import QPixmap, QIcon, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSlot, pyqtSignal, QPoint, QRect
from .logic import MultivisionBackend
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, '..', 'assets')

class SelectionLabel(QLabel):
    area_selected = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.rubberBand.hide()
            rect = self.rubberBand.geometry()
            self.area_selected.emit(rect.x(), rect.y(), rect.width(), rect.height())

class MultivisionClient(QWidget):
    def __init__(self):
        super().__init__()
        self.backend = MultivisionBackend()
        self._draw_ui()
        
        # Connect backend signals
        self.backend.frame_ready.connect(self._on_frame_ready)
        self.backend.zoom_changed.connect(self._on_zoom_changed)
        self.backend.connection_lost.connect(self._on_connection_lost)
        
        # Initial state
        self._on_connection_lost()

    def _draw_ui(self):
        # Layouts
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        zoom_layout = QVBoxLayout()
        move_layout = QGridLayout()
        control_layout = QVBoxLayout()
        # Widgets
        self.video_label = SelectionLabel()
        self.video_label.area_selected.connect(self._on_area_selected)
        self.slider = QSlider(Qt.Vertical)
        self.slider.setMinimum(2)
        self.slider.setMaximum(10)
        self.slider.setSingleStep(1)
        play_button = QPushButton('Play')
        pause_button = QPushButton('Pause')
        
        # Get initial zoom from backend (or default)
        initial_zoom = self.backend.get_current_zoom()
        self.zoom_label = QLabel(str(initial_zoom))
        
        zoom_in_button = QPushButton('+')
        zoom_out_button = QPushButton('-')
        up_button = QPushButton()
        up_button.setIcon(QIcon(os.path.join(ASSETS_DIR, 'up_arrow.png')))
        up_button.setIconSize(QSize(24, 24))
        up_button.setFixedSize(30, 30)
        down_button = QPushButton()
        down_button.setIcon(QIcon(os.path.join(ASSETS_DIR, 'down_arrow.png')))
        down_button.setIconSize(QSize(24, 24))
        down_button.setFixedSize(30, 30)
        left_button = QPushButton()
        left_button.setIcon(QIcon(os.path.join(ASSETS_DIR, 'left_arrow.png')))
        left_button.setIconSize(QSize(24, 24))
        left_button.setFixedSize(30, 30)
        right_button = QPushButton()
        right_button.setIcon(QIcon(os.path.join(ASSETS_DIR, 'right_arrow.png')))
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

        # Functions binding
        play_button.clicked.connect(self.backend.start_stream)
        pause_button.clicked.connect(self.backend.pause_stream)
        zoom_in_button.clicked.connect(self.backend.increase_zoom)
        zoom_out_button.clicked.connect(self.backend.decrease_zoom)
        self.slider.sliderReleased.connect(self._update_zoom_from_slider)
        
        up_button.clicked.connect(self.backend.move_up)
        up_button.setAutoRepeat(True)
        up_button.setAutoRepeatDelay(100)
        up_button.setAutoRepeatInterval(200)
        
        down_button.clicked.connect(self.backend.move_down)
        down_button.setAutoRepeat(True)
        down_button.setAutoRepeatDelay(100)
        down_button.setAutoRepeatInterval(200)
        
        left_button.clicked.connect(self.backend.move_left)
        left_button.setAutoRepeat(True)
        left_button.setAutoRepeatDelay(100)
        left_button.setAutoRepeatInterval(200)
        
        right_button.clicked.connect(self.backend.move_right)
        right_button.setAutoRepeat(True)
        right_button.setAutoRepeatDelay(100)
        right_button.setAutoRepeatInterval(200)
        
        reset_button.clicked.connect(self.backend.move_reset)
        picture_button.clicked.connect(self.backend.take_picture)
        video_button.clicked.connect(self.backend.take_video)

    def _update_zoom_from_slider(self):
        self.backend.set_zoom(self.slider.value())

    @pyqtSlot(QImage)
    def _on_frame_ready(self, qt_image):
        self.video_label.setPixmap(QPixmap.fromImage(qt_image))

    @pyqtSlot(float)
    def _on_zoom_changed(self, zoom):
        self.zoom_label.setText(str(zoom))
        self.slider.blockSignals(True)
        self.slider.setValue(int(zoom * 2))
        self.slider.blockSignals(False)
    
    @pyqtSlot()
    def _on_connection_lost(self):
        pixmap = QPixmap(os.path.join(ASSETS_DIR, "video_error.jpg"))
        self.video_label.setPixmap(pixmap)

    @pyqtSlot(int, int, int, int)
    def _on_area_selected(self, x, y, w, h):
        self.backend.send_selection_area(x, y, w, h, self.video_label.width(), self.video_label.height())
