import sys
from include.gui import SmartvisionClient
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("SmartVision Client")
    stream = SmartvisionClient()
    stream.show()
    sys.exit(app.exec_())
