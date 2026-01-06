import sys
from include.gui import MultivisionClient
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("MultiVision Client")
    stream = MultivisionClient()
    stream.show()
    sys.exit(app.exec_())
