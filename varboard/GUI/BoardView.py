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

        self.squares = [[SquareView(self.frm_main_board, self, square_scale[0], square_scale[1], x, self.board_height - y - 1) for x in range(self.board_width)]
                        for y in range(self.board_height)]
        self.pieces = {}

        self.color_squares(reverse)

        self.set_bars(self)
        self.grid_components()

        # set pieces from current position
        for sq, p in controller.current.pos.pieces_iter():
            self.set_piece(sq, p)

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

    def piece_to_id(self, piece):
        return piece.color.value + piece.ty

    def set_piece(self, pos, piece):
        pos = pos if isinstance(pos, tuple) else pos.to_tuple()
        old = self.pieces.get(pos)
        if piece is None:
            if old:
                old.destroy()
                del self.pieces[pos]
            return
        pimg = PieceView.load_image(f"pieces/{self.piece_to_id(piece)}.svg", self.square_scale)
        if old:
            old.set_image(pimg)
        else:
            self.pieces[pos] = PieceView(self.frm_main_board, self, pimg)
            self.pieces[pos].set_xy(*pos)
            self.pieces[pos].grid(row=(self.board_height - pos[1] - 1), column=pos[0], sticky='NESW', padx=(0, 0), pady=(0, 0))

    def move_piece(self, fpos, tpos):
        fpos = fpos if isinstance(fpos, tuple) else fpos.to_tuple()
        tpos = tpos if isinstance(tpos, tuple) else tpos.to_tuple()
        old = self.pieces[fpos]
        del self.pieces[fpos]
        if tpos in self.pieces:
            self.pieces[tpos].destroy()
        self.pieces[tpos] = old
        self.pieces[tpos].set_xy(*tpos)
        self.pieces[tpos].grid(row=(self.board_height - tpos[1] - 1), column=tpos[0], sticky='NESW', padx=(0, 0), pady=(0, 0))

