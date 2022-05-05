import tkinter as tk
from .widgets import SquareView, PieceView
from typing import Collection, Any

class BoardView(tk.Frame):
    def __init__(self, master, controller, square_scale, reverse=False, white_color='white', black_color='white', *args, **kwargs):
        kwargs['relief'] = kwargs.get('relief', 'raised')
        kwargs['bd'] = kwargs.get('bd', 10)
        super().__init__(master, *args, **kwargs)

        self.square_scale = square_scale

        self.controller = controller

        self.board_height, self.board_width = controller.current.pos.bounds()

        self.white_color = white_color
        self.black_color = black_color

        if reverse:
            self.x_pack_side = tk.RIGHT
            self.y_pack_side = tk.BOTTOM
        else:
            self.x_pack_side = tk.LEFT
            self.y_pack_side = tk.TOP

        # frame for main board with squares in grid
        self.frm_main_board = tk.Frame(master=self, relief=tk.RAISED, bd=6)

        self.squares = [[SquareView(self.frm_main_board, self, square_scale[0], square_scale[1], x, y) for x in range(self.board_width)]
                        for y in range(self.board_height)]
        self.pieces = {}

        self.color_squares(reverse)

        self.set_bars(self)
        self.grid_components()

    def color_squares(self, reverse):
        for row in range(self.board_height):

            self.frm_main_board.columnconfigure(row, weight=1)
            self.frm_main_board.rowconfigure(row, weight=1)
            for column in range(self.board_width):
                padx, pady = (0, 0), (0, 0)

                self.squares[row][column].grid(row=row, column=column, sticky='NESW', padx=padx, pady=pady)

                # setting color of squares
                color1, color2 = self.white_color, self.black_color
                if reverse:
                    color1, color2 = color2, color1

                if abs(row - column) % 2 == 0:
                    self.squares[row][column].set_color(color1)
                else:
                    self.squares[row][column].set_color(color2)

    def set_bars(self, reverse):
        pass

    def grid_components(self):
        pass

    def set_piece(self, x, y, piece):
        old = self.pieces.get((x, y))
        pimg = PieceView.load_image(f"pieces/{piece}.svg", self.square_scale)
        if old:
            old.set_image(pimg)
        else:
            self.pieces[(x, y)] = PieceView(self.frm_main_board, pimg)
            self.pieces[(x, y)].grid(row=(self.board_height - y - 1), column=x, sticky='NESW', padx=(0, 0), pady=(0, 0))

