import asyncio
import random
import sys
from datetime import datetime

import chess
import chess.engine
import chess.pgn
from PySide6.QtCore import QLineF, QPointF, QRectF, Qt
from PySide6.QtGui import (QAction, QBrush, QColor, QPainter, QPen, QPixmap,
                           QPolygonF, QTransform)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import *

SQUARE_SIZE = 70
THEME_COLORS = {
    "dark_square": "#769656",
    "light_square": "#eeeed2",
    "highlight_square": "#d7e81c",
    "highlight_legal_moves": "#3b3b3b",
    "marked_square_ctrl": "#4287f5",
    "marked_square_alt": "#eb4034",
    "marked_square_shift": "#f5a442",
    "arrow_ctrl": "#4287f5",
    "arrow_alt": "#eb4034",
    "arrow_shift": "#f5a442",
}


class StartDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LibreSquares - Choose Options")
        self.setFixedWidth(350)

        self.fischer_random_checkbox = QCheckBox("Use Fischer Random aka chess960")
        self.white_radiobutton = QRadioButton("Play as White")
        self.black_radiobutton = QRadioButton("Play as Black")
        self.white_radiobutton.setChecked(True)

        self.white_engine_checkbox = QCheckBox("Play Engine As White")
        self.black_engine_checkbox = QCheckBox("Play Engine As Black")

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout = QVBoxLayout()
        layout.addWidget(self.fischer_random_checkbox)
        layout.addWidget(self.white_radiobutton)
        layout.addWidget(self.black_radiobutton)
        layout.addWidget(self.white_engine_checkbox)
        layout.addWidget(self.black_engine_checkbox)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_options(self):
        return {
            "fischer_random": self.fischer_random_checkbox.isChecked(),
            "play_as": "white" if self.white_radiobutton.isChecked() else "black",
            "play_engine_as_white": self.white_engine_checkbox.isChecked(),
            "play_engine_as_black": self.black_engine_checkbox.isChecked(),
        }


class ApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LibreSquares")

        # Open dialog box and get user options
        options_dialog = StartDialog()
        if options_dialog.exec() == QDialog.Accepted:
            options = options_dialog.get_options()
        else:
            sys.exit()

        self.fischer_random = options["fischer_random"]
        self.play_as = options["play_as"]
        self.play_engine_as_white = options["play_engine_as_white"]
        self.play_engine_as_black = options["play_engine_as_black"]

        # Initialize chessboard
        self.board = chess.Board(chess960=self.fischer_random)
        if self.fischer_random:
            self.board.set_chess960_pos(random.randint(1, 959))

        # Create chessboard GUI
        self.chessboard = Chessboard(self.board, True)
        self.chessboard.setFixedSize(SQUARE_SIZE * 8.5, SQUARE_SIZE * 8.5)

        if self.play_as == "black":
            self.chessboard.flip_chessboard()

        self.chessboard.engine_play_as_white = self.play_engine_as_white
        self.chessboard.engine_play_as_black = self.play_engine_as_black

        # Create a table widget for displaying moves
        self.move_table = QTableWidget()
        self.move_table.setColumnCount(2)
        self.move_table.setHorizontalHeaderLabels(["White", "Black"])
        self.move_table.setColumnWidth(0, 125)
        self.move_table.setColumnWidth(1, 125)
        self.move_table.setFixedWidth(300)
        self.move_table.setFixedHeight(300)
        self.move_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.move_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.move_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)

        self.move_table.itemClicked.connect(self.chessboard.move_navigator.go_to_move)

        self.chessboard.move_table = self.move_table

        self.pgn_loader = PGNLoader(self.chessboard)

        fen_input = QLineEdit()
        fen_input.setPlaceholderText("Enter a fen string")
        fen_input.setText(self.chessboard.get_chessboard_fen())
        fen_input.setFixedWidth(250)

        load_fen_button = QPushButton("Load Fen")
        load_fen_button.setFixedWidth(150)
        load_fen_button.clicked.connect(
            lambda: self.chessboard.update_chessboard(fen_input.text())
        )

        fen_widget = QWidget()
        fen_layout = QHBoxLayout(fen_widget)
        fen_layout.addWidget(fen_input)
        fen_layout.addWidget(load_fen_button)

        captured_pieces_widget = QWidget()
        captured_pieces_widget_layout = QHBoxLayout(captured_pieces_widget)
        captured_pieces_widget_layout.addWidget(
            self.chessboard.captured_pieces.white_pieces_view
        )
        captured_pieces_widget_layout.addWidget(
            self.chessboard.captured_pieces.black_pieces_view
        )

        # Set up the layout
        main_widget = QWidget()
        layout = QGridLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add widgets to the layout
        layout.addWidget(self.pgn_loader, 0, 0)
        layout.addWidget(self.chessboard, 0, 1)
        layout.addWidget(self.move_table, 0, 2)
        layout.addWidget(fen_widget, 1, 0)
        layout.addWidget(captured_pieces_widget, 1, 1)

        self.setCentralWidget(main_widget)

        # Create a toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        previous_move_action = QAction("Previous Move", self)
        previous_move_action.triggered.connect(
            self.chessboard.move_navigator.previous_move
        )
        toolbar.addAction(previous_move_action)

        next_move_action = QAction("Next Move", self)
        next_move_action.triggered.connect(self.chessboard.move_navigator.next_move)
        toolbar.addAction(next_move_action)

        undo_last_move_action = QAction("Undo Last Move", self)
        undo_last_move_action.triggered.connect(
            self.chessboard.move_navigator.undo_last_move
        )
        toolbar.addAction(undo_last_move_action)

        flip_board_action = QAction("Flip Board", self)
        flip_board_action.triggered.connect(self.chessboard.flip_chessboard)
        toolbar.addAction(flip_board_action)

        reset_game_action = QAction("Reset Game", self)
        reset_game_action.triggered.connect(self.chessboard.reset_game)
        toolbar.addAction(reset_game_action)

        self.set_initial_engine_move()

    def set_initial_engine_move(self):
        if self.play_engine_as_white:
            self.chessboard.make_engine_move()


class Chessboard(QGraphicsView):
    def __init__(self, board, show_labels=True):
        super().__init__()
        self.board = board
        self.show_labels = show_labels
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        # Enable antialiasing for smooth rendering
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self.move_manager = MoveManager(self)
        self.move_navigator = MoveNavigator(self)
        self.captured_pieces = CapturedPieces()
        self.is_navigating_moves = False  # Flag to indicate if user is navigating moves
        self.is_board_flipped = False  # Flag to indicate if the board is flipped
        self.is_piece_moved = False  # Flag to indicate if piece has been moved
        self.marked_squares = {}
        self.arrows = []
        self.is_drawing_arrow = False  # Flag to indicate if user is drawing arrow
        self.start_pos = QPointF(0, 0)
        self.end_pos = QPointF(0, 0)
        self.arrow_color = None
        self.engine = None
        self.engine_play_as_white = False
        self.engine_play_as_black = False
        self.chess_pieces = ChessPieces(
            self, self.scene, self.is_board_flipped, "cardinal"
        )
        self.chess_pieces.load_chess_piece_images()

        self.draw_chessboard()

    async def engine_move(self):
        engine_options = {
            "Skill Level": 10,
            "UCI_Elo": 1399,
        }
        if not self.engine_play_as_white or not self.engine_play_as_black:
            transport, self.engine = await chess.engine.popen_uci("engine/stockfish")
        result = await self.engine.play(
            self.board, chess.engine.Limit(time=0.1, depth=1), options=engine_options
        )
        self.move_navigator.get_san_move(result.move)
        self.board.push(result.move)
        self.is_piece_moved = True
        await self.engine.quit()
        self.engine = None

    def make_engine_move(self):
        if (self.engine_play_as_white and self.board.turn == chess.WHITE) or (
            self.engine_play_as_black and self.board.turn == chess.BLACK
        ):
            asyncio.run(self.engine_move())
            self.after_move_ops()

    def after_move_ops(self):
        """
        do some operations after move has been made
        """
        if self.is_piece_moved:
            self.move_navigator.update_moves()
            self.move_navigator.update_move_table()
            self.move_manager.selected_square = None
            self.delete_arrows()
            self.delete_marked_squares()
            self.delete_highlighted_squares()
            self.highlight_source_and_destination_squares()
            self.chess_pieces.delete_pieces()
            self.chess_pieces.draw_pieces()
            self.delete_highlighted_legal_moves()

    def get_square_coordinates(self, square):
        """
        col, row, x, y = self.get_square_coordinates(square)
        """
        if self.is_board_flipped:
            col = 7 - chess.square_file(square)
            row = chess.square_rank(square)
        else:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
        return col, row, col * SQUARE_SIZE, row * SQUARE_SIZE

    def draw_squares(self):
        """
        draws squares forming a chessboard
        """
        for square in chess.SQUARES:
            col, row, x, y = self.get_square_coordinates(square)

            rect = self.scene.addRect(x, y, SQUARE_SIZE, SQUARE_SIZE)

            rect_color = (
                THEME_COLORS["light_square"]
                if (row + col) % 2 == 0
                else THEME_COLORS["dark_square"]
            )

            rect.setPen(Qt.NoPen)
            rect.setBrush(QColor(rect_color))

    def draw_labels(self):
        """
        draws rank and file label. a-h,1-8
        """
        for square in chess.SQUARES:
            col, row, x, y = self.get_square_coordinates(square)

            # Determine label position
            row_label_x = x + SQUARE_SIZE / 8 - 10
            row_label_y = y + SQUARE_SIZE / 8 - 10

            col_label_x = x + SQUARE_SIZE - SQUARE_SIZE / 15 - 10
            col_label_y = y + SQUARE_SIZE - SQUARE_SIZE / 8 - 15

            label_color = (
                THEME_COLORS["light_square"]
                if (row + col) % 2 != 0
                else THEME_COLORS["dark_square"]
            )

            if self.show_labels:
                # Add label for the first set of columns (a-h)
                if row == 7:
                    if self.is_board_flipped:
                        label = self.scene.addText(f'{chr(ord("h")-col)}')
                    else:
                        label = self.scene.addText(f'{chr(ord("a")+col)}')
                    label.setDefaultTextColor(QColor(label_color))
                    label.setPos(col_label_x, col_label_y)

                # Add label for the first set of rows (1-8)
                if col == 0:
                    if self.is_board_flipped:
                        label = self.scene.addText(f"{row+1}")
                    else:
                        label = self.scene.addText(f"{8-row}")
                    label.setDefaultTextColor(QColor(label_color))
                    label.setPos(row_label_x, row_label_y)

    def draw_chessboard(self):
        self.scene.clear()
        self.draw_squares()
        self.draw_labels()
        self.highlight_source_and_destination_squares()
        self.chess_pieces.draw_pieces()

    def flip_chessboard(self):
        self.is_board_flipped = not self.is_board_flipped
        self.chess_pieces.flipped = self.is_board_flipped
        self.draw_chessboard()

    def update_chessboard(self, fen):
        self.board.set_fen(fen)
        self.draw_chessboard()

    def reset_game(self):
        self.board.reset()
        self.board.clear_stack()
        self.move_navigator.moves_made.clear()
        self.move_navigator.moves_made_san.clear()
        self.move_table.setRowCount(0)
        self.draw_chessboard()

    def delete_highlighted_squares(self):
        items = self.scene.items()
        for item in items:
            if isinstance(item, QGraphicsRectItem):
                brush_color = item.brush().color()
                if brush_color == QColor(THEME_COLORS["highlight_square"]):
                    self.scene.removeItem(item)

    def delete_highlighted_legal_moves(self):
        items = self.scene.items()
        for item in items:
            if isinstance(item, QGraphicsEllipseItem):
                brush_color = item.brush().color()
                if brush_color == QColor(THEME_COLORS["highlight_legal_moves"]):
                    self.scene.removeItem(item)

    def get_square_number_at_pos(self, event):
        pos = event.position().toPoint()
        mapped_pos = self.mapToScene(pos)
        col = int(mapped_pos.x() / SQUARE_SIZE)
        row = int(mapped_pos.y() / SQUARE_SIZE)
        if self.is_board_flipped:
            return chess.square(7 - col, row)

        return chess.square(col, 7 - row)

    def draw_arrow(self):
        arrow = Arrow(self.start_pos, self.end_pos, self.arrow_color)
        self.scene.addItem(arrow)

    def delete_arrows(self):
        for arrow in self.arrows:
            self.scene.removeItem(arrow)
        self.arrows = []
        self.scene.update()

    def highlight_legal_moves(self, square):
        """
        highlights the legal moves of a selected piece
        """
        legal_moves = self.move_manager.get_legal_moves(square)

        for target_square in set(move.to_square for move in legal_moves):
            col, row, x, y = self.get_square_coordinates(target_square)

            # Add a circle in the center of the square
            circle = self.scene.addEllipse(
                x + SQUARE_SIZE / 4,
                y + SQUARE_SIZE / 4,
                SQUARE_SIZE / 2,
                SQUARE_SIZE / 2,
            )
            circle.setPen(Qt.NoPen)
            circle.setBrush(QColor(THEME_COLORS["highlight_legal_moves"]))
            circle.setOpacity(0.45)

    def create_highlighted_square(self, square, color):
        """
        creates the rect at the source and destination squares
        """
        rect = QGraphicsRectItem()
        rect.setRect(
            square[0] * SQUARE_SIZE,
            square[1] * SQUARE_SIZE,
            SQUARE_SIZE,
            SQUARE_SIZE,
        )
        rect.setPen(Qt.NoPen)
        rect.setBrush(QColor(color))
        rect.setOpacity(0.45)
        return self.scene.addItem(rect)

    def create_marked_square(self, square, color):
        """
        creates the rect at the given pos.
        """
        if square in self.marked_squares:
            return

        col, row, x, y = self.get_square_coordinates(square)

        # Check if there is already a rectangle at the given position
        existing_rects = self.scene.items(QRectF(x, y, SQUARE_SIZE, SQUARE_SIZE))
        for rect in existing_rects:
            if isinstance(rect, QGraphicsRectItem):
                brush_color = rect.brush().color()
                if brush_color == QColor(color):
                    return

        rect = self.scene.addRect(x, y, SQUARE_SIZE, SQUARE_SIZE)
        rect.setPen(Qt.NoPen)
        rect.setBrush(QColor(color))
        rect.setOpacity(0.90)
        self.marked_squares[square] = rect

    def delete_marked_square(self, square):
        if square in self.marked_squares:
            rect = self.marked_squares[square]
            self.scene.removeItem(rect)
            del self.marked_squares[square]

    def delete_marked_squares(self):
        for square, rect in self.marked_squares.items():
            self.scene.removeItem(rect)
        self.marked_squares.clear()

    def highlight_source_and_destination_squares(self):
        if self.board.move_stack:
            last_move = self.board.move_stack[-1]
            source_square = self.move_manager.get_source_square_from_move(last_move)
            destination_square = self.move_manager.get_destination_square_from_move(
                last_move
            )
            self.create_highlighted_square(
                source_square, THEME_COLORS["highlight_square"]
            )
            self.create_highlighted_square(
                destination_square, THEME_COLORS["highlight_square"]
            )

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self.is_navigating_moves:
            square_number = self.get_square_number_at_pos(event)
            piece = self.board.piece_at(square_number)

            if self.move_manager.selected_square is None:
                self.move_manager.select_square(square_number)
            else:
                if square_number == self.move_manager.selected_square:
                    self.move_manager.selected_square = None
                    self.delete_highlighted_legal_moves()
                    return

                self.move_manager.move_piece(square_number)
                self.after_move_ops()
                self.make_engine_move()

        if event.buttons() == Qt.LeftButton:
            modifiers = event.modifiers()
            if modifiers == Qt.ControlModifier:
                self.arrow_color = QColor(THEME_COLORS["arrow_ctrl"])
            elif modifiers == Qt.AltModifier:
                self.arrow_color = QColor(THEME_COLORS["arrow_alt"])
            elif modifiers == Qt.ShiftModifier:
                self.arrow_color = QColor(THEME_COLORS["arrow_shift"])
            else:
                return
            if not self.is_drawing_arrow:
                self.is_drawing_arrow = True
                self.move_manager.selected_square = None
                self.delete_highlighted_legal_moves()

                square_number = self.get_square_number_at_pos(event)
                col, row, x, y = self.get_square_coordinates(square_number)
                self.start_pos = QPointF(x + SQUARE_SIZE / 2, y + SQUARE_SIZE / 2)
                self.end_pos = QPointF(x + SQUARE_SIZE / 2, y + SQUARE_SIZE / 2)

        if event.button() == Qt.RightButton:
            square_number = self.get_square_number_at_pos(event)
            self.delete_marked_square(square_number)

            modifiers = event.modifiers()
            if modifiers == Qt.ControlModifier:
                self.create_marked_square(
                    square_number, THEME_COLORS["marked_square_ctrl"]
                )
            elif modifiers == Qt.AltModifier:
                self.create_marked_square(
                    square_number, THEME_COLORS["marked_square_alt"]
                )
            elif modifiers == Qt.ShiftModifier:
                self.create_marked_square(
                    square_number, THEME_COLORS["marked_square_shift"]
                )
            else:
                return
            self.chess_pieces.delete_pieces()
            self.chess_pieces.draw_pieces()

    def mouseMoveEvent(self, event):
        if self.is_drawing_arrow:
            square_number = self.get_square_number_at_pos(event)
            col, row, x, y = self.get_square_coordinates(square_number)
            self.end_pos = QPointF(x + SQUARE_SIZE / 2, y + SQUARE_SIZE / 2)
            self.scene.update()

    def mouseReleaseEvent(self, event):
        if self.is_drawing_arrow:
            self.is_drawing_arrow = False
            self.draw_arrow()
            self.scene.update()

    def next_move(self):
        self.move_navigator.next_move()

    def previous_move(self):
        self.move_navigator.previous_move()

    def game_result(self, board):
        if board.is_checkmate():
            GameResult.show_checkmate()
        elif board.is_stalemate():
            GameResult.show_stalemate()

    def get_chessboard_fen(self):
        return self.board.fen()

    def update_captured_pieces(self, move):
        capture_piece = self.board.is_capture(move)
        if capture_piece:
            captured_piece = self.board.piece_at(move.to_square)
            if captured_piece:
                self.captured_pieces.add_piece(captured_piece)
        if self.board.is_en_passant(move):  # Handle en passant captures
            target_square = self.board.ep_square
            captured_piece_square = chess.square(
                chess.square_file(target_square), chess.square_rank(move.from_square)
            )
            captured_piece = self.board.piece_at(captured_piece_square)
            if captured_piece:
                self.captured_pieces.add_piece(captured_piece)


class CapturedPieces(QWidget):
    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.white_pieces_view = QGraphicsView()
        white_pieces_scene = QGraphicsScene(self.white_pieces_view)
        self.white_pieces_view.setScene(white_pieces_scene)
        self.white_pieces_view.setFixedWidth(200)
        self.white_pieces_view.setFixedHeight(60)
        layout.addWidget(self.white_pieces_view)

        self.black_pieces_view = QGraphicsView()
        black_pieces_scene = QGraphicsScene(self.black_pieces_view)
        self.black_pieces_view.setScene(black_pieces_scene)
        self.black_pieces_view.setFixedWidth(200)
        self.black_pieces_view.setFixedHeight(60)
        layout.addWidget(self.black_pieces_view)

    def add_piece(self, captured_piece):
        piece_color = "w" if captured_piece.color == chess.WHITE else "b"
        piece_name = captured_piece.symbol().upper()

        image_path = f"assets/pieces/cardinal/{piece_color}{piece_name}.svg"
        renderer = QSvgRenderer(image_path)

        pixmap = QPixmap(SQUARE_SIZE - 10, SQUARE_SIZE - 10)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        pixmap = pixmap.scaledToHeight(SQUARE_SIZE / 2, Qt.SmoothTransformation)

        piece_item = QGraphicsPixmapItem(pixmap)
        if piece_color == "w":
            self.white_pieces_view.scene().addItem(piece_item)
            piece_item.setPos(
                len(self.white_pieces_view.scene().items()) * SQUARE_SIZE / 2, 0
            )
        else:
            self.black_pieces_view.scene().addItem(piece_item)
            piece_item.setPos(
                len(self.black_pieces_view.scene().items()) * SQUARE_SIZE / 2, 0
            )


class MoveNavigator:
    def __init__(self, chessboard):
        self.moves_made = []
        self.moves_made_san = []
        self.chessboard = chessboard
        self.current_move_index = 0

    def update_moves(self):
        self.moves_made.clear()
        self.moves_made.extend(self.chessboard.board.move_stack)
        self.current_move_index = len(self.moves_made) - 1

    def undo_last_move(self):
        self.moves_made.pop()
        self.moves_made_san.pop()
        self.chessboard.board.pop()
        self.update_moves()
        # Delete the last row from the move table
        if len(self.moves_made) % 2 == 0:
            self.chessboard.move_table.removeRow(len(self.moves_made) // 2 - 1)
        self.update_move_table()
        self.chessboard.delete_highlighted_squares()
        self.chessboard.highlight_source_and_destination_squares()
        self.chessboard.chess_pieces.delete_pieces()
        self.chessboard.chess_pieces.draw_pieces()

    def next_move(self):
        if self.current_move_index < len(self.moves_made) - 1:
            self.chessboard.is_navigating_moves = True
            self.current_move_index += 1
            move = self.moves_made[self.current_move_index]
            self.chessboard.board.push(move)

            self.chessboard.delete_highlighted_squares()
            self.chessboard.highlight_source_and_destination_squares()

            self.chessboard.chess_pieces.delete_pieces()
            self.chessboard.chess_pieces.draw_pieces()

            # Check if the user has reached the last move
            if self.current_move_index == len(self.moves_made) - 1:
                self.chessboard.is_navigating_moves = False

    def previous_move(self):
        if self.current_move_index >= 0:
            self.chessboard.is_navigating_moves = True
            self.chessboard.board.pop()
            self.current_move_index -= 1

            self.chessboard.delete_highlighted_squares()
            self.chessboard.highlight_source_and_destination_squares()

            self.chessboard.chess_pieces.delete_pieces()
            self.chessboard.chess_pieces.draw_pieces()

    def get_san_move(self, move):
        return self.moves_made_san.append(self.chessboard.board.san(move))

    def update_move_table(self):
        self.chessboard.move_table.clearContents()
        num_moves = len(self.moves_made)
        num_rows = num_moves // 2 if num_moves % 2 == 0 else num_moves // 2 + 1

        while self.chessboard.move_table.rowCount() < num_rows:
            self.chessboard.move_table.insertRow(self.chessboard.move_table.rowCount())

        for i, move in enumerate(self.moves_made_san):
            row = i // 2
            col = i % 2
            if (
                row >= self.chessboard.move_table.rowCount()
                or col >= self.chessboard.move_table.columnCount()
            ):
                continue
            item = self.chessboard.move_table.item(row, col)
            if item is None:
                item = QTableWidgetItem(move)
                self.chessboard.move_table.setItem(row, col, item)
            else:
                item.setText(move)

    def go_to_move(self, item):
        row = item.row()
        col = item.column()
        index = row * 2 + col
        if 0 <= index < len(self.moves_made):
            while index < self.current_move_index:
                self.previous_move()
            while index > self.current_move_index:
                self.next_move()


class MoveManager:
    def __init__(self, chessboard):
        self.chessboard = chessboard
        self.selected_square = None

    def select_square(self, square):
        if square is not None:
            piece = self.chessboard.board.piece_at(square)

            if piece is not None and piece.color == self.chessboard.board.turn:
                self.selected_square = square
                self.chessboard.highlight_legal_moves(square)

    def get_destination_square_from_move(self, move):
        if self.chessboard.is_board_flipped:
            return (
                7 - chess.square_file(move.to_square),
                chess.square_rank(move.to_square),
            )
        return chess.square_file(move.to_square), 7 - chess.square_rank(move.to_square)

    def get_source_square_from_move(self, move):
        if self.chessboard.is_board_flipped:
            return (
                7 - chess.square_file(move.from_square),
                chess.square_rank(move.from_square),
            )
        return chess.square_file(move.from_square), 7 - chess.square_rank(
            move.from_square
        )

    def get_legal_moves(self, square):
        moves = []
        for move in self.chessboard.board.legal_moves:
            if move.from_square == square:
                moves.append(move)
        return moves

    def move_piece(self, target_square):
        if self.selected_square is not None:
            for move in self.chessboard.board.legal_moves:
                if (
                    move.from_square == self.selected_square
                    and move.to_square == target_square
                ):
                    if self.chessboard.board.piece_type_at(
                        self.selected_square
                    ) == chess.PAWN and (
                        (
                            self.chessboard.board.turn == chess.WHITE
                            and chess.square_rank(target_square) == 7
                        )
                        or (
                            self.chessboard.board.turn == chess.BLACK
                            and chess.square_rank(target_square) == 0
                        )
                    ):
                        self.handle_pawn_promotion(move)
                    self.chessboard.move_navigator.get_san_move(move)
                    self.chessboard.get_chessboard_fen()
                    self.chessboard.update_captured_pieces(move)
                    self.chessboard.board.push(move)
                    self.chessboard.game_result(self.chessboard.board)
                    self.chessboard.highlight_legal_moves(target_square)
                    self.chessboard.is_piece_moved = True

                    break

    def handle_pawn_promotion(self, move):
        piece_options = ["Queen", "Rook", "Knight", "Bishop"]

        dialog = QDialog(self.chessboard)
        dialog.setModal(True)
        dialog.setWindowTitle("Promote Pawn")
        dialog.setFixedWidth(300)

        layout = QVBoxLayout(dialog)
        dialog.setLayout(layout)

        # Create a button for each piece option
        for piece in piece_options:
            button = QPushButton(piece)
            button.clicked.connect(
                lambda move=move, piece=piece: self.promote_pawn(dialog, move, piece)
            )
            layout.addWidget(button)

        dialog.exec()

    def promote_pawn(self, dialog, move, piece):
        piece_map = {
            "Queen": chess.QUEEN,
            "Rook": chess.ROOK,
            "Knight": chess.KNIGHT,
            "Bishop": chess.BISHOP,
        }
        move.promotion = piece_map[piece]

        dialog.accept()  # Close the dialog after promoting the pawn


class ChessPieces:
    def __init__(self, chessboard, scene, flipped, piece_set="img"):
        self.chessboard = chessboard
        self.scene = scene
        self.flipped = flipped
        self.piece_images = {}
        self.piece_set = piece_set

    def load_chess_piece_images(self):
        piece_names = ["P", "N", "B", "R", "Q", "K"]
        for piece_name in piece_names:
            piece_image_paths = {
                "w": f"assets/pieces/{self.piece_set}/w{piece_name}.svg",
                "b": f"assets/pieces/{self.piece_set}/b{piece_name}.svg",
            }
            for piece_color, image_path in piece_image_paths.items():
                renderer = QSvgRenderer(image_path)
                pixmap = QPixmap(SQUARE_SIZE - 10, SQUARE_SIZE - 10)
                pixmap.fill(Qt.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                self.piece_images[(piece_color, piece_name)] = pixmap

    def draw_pieces(self):
        piece_list = self.chessboard.board.fen().split()[0]
        square = 0
        for char in piece_list:
            if char.isdigit():
                square += int(char)
            elif char != "/":
                piece_name = char.upper()
                piece_color = "w" if char.isupper() else "b"
                if self.flipped:
                    x = (7 - square % 8) * SQUARE_SIZE + 5
                    y = (7 - square // 8) * SQUARE_SIZE + 5
                else:
                    x = (square % 8) * SQUARE_SIZE + 5
                    y = (square // 8) * SQUARE_SIZE + 5

                piece_item = QGraphicsPixmapItem(
                    self.piece_images[(piece_color, piece_name)]
                )
                piece_item.setPos(x, y)
                self.scene.addItem(piece_item)

                square += 1

    def delete_pieces(self):
        items = self.scene.items()
        for item in items:
            if isinstance(item, QGraphicsPixmapItem):
                self.scene.removeItem(item)


class Arrow(QGraphicsItem):
    def __init__(self, start_pos, end_pos, arrow_color):
        super().__init__()
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.arrow_color = arrow_color

    def boundingRect(self):
        return QRectF(self.start_pos, self.end_pos).normalized()

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        pen = QPen(QColor(self.arrow_color), 3.5)
        pen.setCapStyle(Qt.RoundCap)
        brush = QBrush(QColor(self.arrow_color))
        painter.setPen(pen)
        painter.setBrush(brush)

        line = QLineF(self.start_pos, self.end_pos)
        painter.drawLine(line)

        arrow_head_length = 10

        # Check if line length is non-zero before performing division
        if line.length() != 0:
            arrow_line_length = line.length() - arrow_head_length
            angle = line.angle()
            arrow_point = line.p2()

            arrow_line1 = QLineF()
            arrow_line1.setP1(QPointF(line.pointAt(arrow_line_length / line.length())))
            arrow_line1.setAngle(angle + 180 - 45)
            arrow_line1.setLength(arrow_head_length)

            arrow_line2 = QLineF()
            arrow_line2.setP1(QPointF(line.pointAt(arrow_line_length / line.length())))
            arrow_line2.setAngle(angle + 180 + 45)
            arrow_line2.setLength(arrow_head_length)

            arrow_head = QPolygonF()
            arrow_head.append(arrow_line1.p2())
            arrow_head.append(arrow_point)
            arrow_head.append(arrow_line2.p2())

            painter.drawPolygon(arrow_head)


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


class GameResult:
    @staticmethod
    def show_checkmate():
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Game Result")
        msg_box.setText("Checkmate!")
        msg_box.exec()

    @staticmethod
    def show_stalemate():
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Game Result")
        msg_box.setText("Stalemate!")
        msg_box.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ApplicationWindow()
    window.showMaximized()
    sys.exit(app.exec())
