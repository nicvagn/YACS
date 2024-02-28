from chessboard import DrawChessBoard
from pgnmanager import DrawPgn
import sys
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import *

import vars

import chess


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.__version__ = vars.VERSION
        self.setWindowTitle(f"YACS - Yet Another Chess Software ({self.__version__})")
        # hack for pgn 
        self.pyboard = chess.Board()
        self.chess_board = DrawChessBoard()

        self.pgnDock = DrawPgn()
        self.setCentralWidget(self.chess_board)

        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.pgnDock)

        self.chess_board.draw_chessboard()
        self.chess_board.setFixedSize(vars.SQUARE_SIZE * 8.5, vars.SQUARE_SIZE * 8.5)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ApplicationWindow()
    window.showMaximized()
    sys.exit(app.exec())
