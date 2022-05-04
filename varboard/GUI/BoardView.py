import tkinter as tk
from .SquareView import Square
from .PieceView import Piece


class BoardView(tk.Frame):
    def __init__(self, master, board, square_height, square_width, reverse=False, white_color='white', black_color='white', *args, **kwargs):
        kwargs['relief'] = kwargs.get('relief', 'raised')
        kwargs['bd'] = kwargs.get('bd', 10)
        super().__init__(master, *args, **kwargs)

        self.square_height = square_height
        self.square_width = square_width

        self.board_height = len(board)
        self.board_width = len(board[0])

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

        self.squares = [[Square(self.frm_main_board, self, square_height, square_width) for _ in range(self.board_width)]
                        for _ in range(self.board_height)]

        self.color_squares(reverse)

        self.set_bars(self)
        self.grid_components()

    def set_square_image(self, row, column, pimg):
        self.squares[row][column].set_image(pimg)

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
                    self.squares[row][column].set_background(color1)
                else:
                    self.squares[row][column].set_background(color2)

    def set_bars(self, reverse):
        pass

    def grid_components(self):
        pass


if __name__ == '__main__':
    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    board = [[None for _ in range(8)] for _ in range(8)]
    board_view = BoardView(window, board, scale[0], scale[1], reverse=False)
    print(board_view.tk)
    pieces = {'bK': Piece('pieces/bK.svg', scale),
              'wN': Piece('pieces/wN.svg', scale),
              'bR': Piece('pieces/bR.svg', scale),
              'wK': Piece('pieces/wK.svg', scale)}
    board_view.squares[1][0].set_piece(pieces['bK'])
    board_view.squares[1][1].set_piece(pieces['wN'])
    board_view.squares[6][5].set_piece(pieces['bR'])
    board_view.squares[5][4].set_piece(pieces['wK'])

    board_view.pack()
    window.mainloop()
