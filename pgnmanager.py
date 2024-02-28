#   This file is part of YACS
#
#   YACS free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#   YACS is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along with YACS. If not, see <https://www.gnu.org/licenses/>. 

from PySide6 import QtWidgets

from PySide6.QtWidgets import *
import chess


class DrawPgn(QtWidgets.QDockWidget):
    def __init__(self, chessboard):
        # chessboard should be the chessboard.py instance this pgn is associated with
        super().__init__()

        # Create a table widget for displaying moves
        self.move_table = QTableWidget()
        self.move_table.setColumnCount(2)
        self.move_table.setRowCount(33)
        self.move_table.setHorizontalHeaderLabels(["White", "Black"])
        self.move_table.setColumnWidth(0, 125)
        self.move_table.setColumnWidth(1, 125)
        self.move_table.setFixedWidth(300)
        self.move_table.setFixedHeight(300)
        self.move_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.move_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.move_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)


        self.exItem = QTableWidgetItem()

        self.move_table.setItem(1,1,self.exItem)
        # set the move table as the widget in this dock
        self.setWidget(self.move_table)

        # the move number we are on
        self.move_num = 0
        # because I am bad at math and marginal at itteration
        self.column_1 = True

        # needed for translation into san
        self.san_pig = chessboard.get_internal_board()


        #self.move_table.itemClicked.connect(self.chessboard.move_navigator.go_to_move)
    def push_move(self, move) -> None:
        print(move)

        row = self.move_num // 2 

        if self.column_1:
            column = 0
        else:
            column = 1
        breakpoint()
        move_widget = QTableWidgetItem(self.san_pig.san(move))
        
        self.move_table.setItem(0, column, move_widget) 
        # set to other column
        self.column_1 = not self.column_1



class PGNManager(QtWidgets.QDockWidget):
    """manages the PGN for a chess game"""

    def __init__(self, board: chess.Board()):
        self.game = game 
        pass



    



"""
class PGNLoader(QWidget):
    def __init__(self, chessboard):
        super().__init__()
        self.chessboard = chessboard

        self.games_list = QListWidget()
        self.games_list.setFixedWidth(300)
        self.games_list.itemClicked.connect(self.load_game)

        load_pgn_button = QPushButton("Import PGN")
        load_pgn_button.setFixedWidth(300)
        load_pgn_button.clicked.connect(self.open_pgn_file)

        layout = QVBoxLayout()
        layout.addWidget(self.games_list)
        layout.addWidget(load_pgn_button)

        self.setLayout(layout)

    def open_pgn_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select PGN File", "", "PGN Files (*.pgn)"
        )
        if file_path:
            self.list_pgn_games(file_path)

    def list_pgn_games(self, file_path):
        self.games_list.clear()
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                pgn_game = chess.pgn.read_game(file)
                while pgn_game:
                    item = QListWidgetItem(
                        f"{pgn_game.headers['White']} vs {pgn_game.headers['Black']} - ({pgn_game.headers['Result']})"
                    )
                    item.setData(Qt.UserRole, pgn_game)
                    self.games_list.addItem(item)
                    pgn_game = chess.pgn.read_game(file)
                self.chessboard.move_table.setRowCount(0)
        except FileNotFoundError:
            print("File not found.")

    def load_game(self, item):
        pgn_game = item.data(Qt.UserRole)
        self.chessboard.reset_game()

        for move in pgn_game.mainline_moves():
            self.chessboard.move_navigator.get_san_move(move)
            self.chessboard.board.push(move)

        self.chessboard.move_navigator.update_moves()
        self.chessboard.move_navigator.update_move_table()
"""
