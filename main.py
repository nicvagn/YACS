from pgnmanager import DrawPgn
import sys

import sys

from PySide6 import QtGui, QtWidgets, QtCore

from PySide6.QtCore import *
import config
from chessboard import DrawChessBoard

import chess


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.__version__ = config.VERSION
        self.setWindowTitle(f"YACS - Yet Another Chess Software ({self.__version__})")
        # hack for pgn 
        self.pyboard = chess.Board()
        self.chess_board = DrawChessBoard()

        self.pgnDock = DrawPgn()
        self.setCentralWidget(self.chess_board)

        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.pgnDock)

        self.chess_board.draw_chessboard()
        self.chess_board.setFixedSize(
            config.SQUARE_SIZE * 8.5, config.SQUARE_SIZE * 8.5
        )

        # Create a toolbar
        toolbar = QtWidgets.QToolBar()
        self.addToolBar(toolbar)

        flip_board_action = QtGui.QAction("Flip Board", self)
        flip_board_action.triggered.connect(self.chess_board.flip_chessboard)
        toolbar.addAction(flip_board_action)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ApplicationWindow()
    window.showMaximized()
    sys.exit(app.exec())
