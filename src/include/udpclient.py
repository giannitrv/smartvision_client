from PyQt5.QtCore import QObject, pyqtSignal, QByteArray
from PyQt5.QtNetwork import QUdpSocket, QHostAddress

class UdpClient(QObject):
    data_received = pyqtSignal(QByteArray)

    def __init__(self, source_ip, remote_port, local_port):
        super().__init__()
        self.source_ip = source_ip
        self.remote_port = int(remote_port)
        self.sock = QUdpSocket(self)
        self.is_bound = self.sock.bind(QHostAddress.Any, local_port)
        self.sock.readyRead.connect(self._read_pending_datagrams)

    def is_ready(self):
        return self.is_bound and self.sock.state() == QUdpSocket.BoundState and self.source_ip != 0

    def send_message(self, message):
        if self.is_ready():
            self.sock.writeDatagram(message, QHostAddress(self.source_ip), self.remote_port)

    def _read_pending_datagrams(self):
        while self.sock.hasPendingDatagrams():
            datagram_size = self.sock.pendingDatagramSize()
            datagram = self.sock.receiveDatagram(datagram_size)
            self.data_received.emit(datagram.data())
