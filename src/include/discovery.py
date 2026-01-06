from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtNetwork import QUdpSocket, QHostAddress, QNetworkDatagram

class UDPDiscovery(QObject):
    data_received = pyqtSignal(QNetworkDatagram)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.socket = QUdpSocket(self)
        # Bind to port 6000
        self.socket.bind(QHostAddress.Any, 6000)
        # Connect the readyRead signal to our handler
        self.socket.readyRead.connect(self.process_pending_datagrams)

    def process_pending_datagrams(self):
        while self.socket.hasPendingDatagrams():
            # Receive the datagram
            datagram = self.socket.receiveDatagram()
            self.data_received.emit(datagram)

