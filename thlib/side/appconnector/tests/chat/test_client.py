import sys
import os
import logging
sys.path.insert(0, os.path.abspath(__file__).replace("\\", "/").rsplit("/", 4)[0])
from appconnector.qt import QtWidgets, QtGui, QtCore
from appconnector.client import Client, logger


def test(connect=False):
    logger.setLevel(logging.DEBUG)

    client = Client("127.0.0.1", -1)

    timer = QtCore.QTimer()
    timer.setSingleShot(True)

    def test_timer_receive(data):

        timer.start(3000)

    def test_timer_send():

        client.send("system:hello, i`m the client".encode("utf-8"))

    def test_connect():

        client.send("system:hello".encode("utf-8"))

    timer.timeout.connect(test_timer_send)
    client.connected.connect(test_connect)
    client.received.connect(test_timer_receive)

    found_app = QtWidgets.QApplication.instance()
    if not found_app:
        app = QtWidgets.QApplication(sys.argv)

    else:
        app = found_app

    window = QtWidgets.QWidget()
    window.setWindowTitle("client")
    layout = QtWidgets.QVBoxLayout()
    window.setLayout(layout)

    plain_text = QtWidgets.QPlainTextEdit()
    plain_text.setMinimumHeight(180)
    plain_text.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    layout.addWidget(plain_text)

    text = QtWidgets.QLineEdit()
    text.setPlaceholderText("Insert message and press enter")
    layout.addWidget(text)

    def test_send():

        data = text.text()
        text.clear()
        client.send(data.encode("utf-8"))

        plain_text.moveCursor(QtGui.QTextCursor.End)
        plain_text.appendHtml("<font color=\"red\">" + str(data) + "</font>")

    def test_receive(data):

        plain_text.moveCursor(QtGui.QTextCursor.End)
        datab = bytes(data)
        try:
            datas = datab.decode("utf-8")

        except:
            print("\nerror!!!")
            print(datab)
            datas = ""

        if datas.startswith("system:"):
            plain_text.appendHtml("<font color=\"gray\">" + str(datas) + "</font>")
        else:
            plain_text.appendHtml("<font color=\"black\">" + str(datas) + "</font>")

    def test_spam():

        data = text.text()

        for i in range(3):
            client.send(data.encode("utf-8"))

            plain_text.moveCursor(QtGui.QTextCursor.End)
            plain_text.appendHtml("<font color=\"red\">" + str(data) + "</font>")

    client.received.connect(test_receive)

    text.returnPressed.connect(test_send)

    spbutton = QtWidgets.QPushButton("SPAM")
    spbutton.released.connect(test_spam)
    layout.addWidget(spbutton)

    sbutton = QtWidgets.QPushButton("CONNECT")
    layout.addWidget(sbutton)

    ebutton = QtWidgets.QPushButton("DISCONNECT")
    ebutton.setVisible(False)
    layout.addWidget(ebutton)
    window.show()

    def test_disconnected():

        ebutton.setVisible(False)
        sbutton.setVisible(True)

    def test_connected():

        ebutton.setVisible(True)
        sbutton.setVisible(False)

    client.connected.connect(test_connected)
    client.disconnected.connect(test_disconnected)

    def test_close():

        client.close()

    def test_open():

        client.open()

    sbutton.released.connect(test_open)
    ebutton.released.connect(test_close)

    if connect:
        test_open()

    if not found_app:
        sys.exit(app.exec_())

    return window


if __name__ == "__main__":
    test()
