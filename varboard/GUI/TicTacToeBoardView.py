from .BoardView import *


class TicTacToeBoardView(BoardView):
    def __init__(self, master, board, square_height, square_width, reverse=False, white_color='white', black_color='white', *args, **kwargs):
        super().__init__(master, board, square_height, square_width, reverse, white_color, black_color, *args, **kwargs)
        self.o_piece = Piece('GUI/pieces/o.svg', (self.square_height-5, self.square_width-5))
        self.x_piece = Piece('GUI/pieces/x.svg', (self.square_height-5, self.square_width-5))
        self.o = True

    def grid_components(self):
        self.frm_main_board.grid(row=0, column=0)

    def handle_square_btn(self, square):
        if self.o:
            square.set_piece(self.o_piece)
        else:
            square.set_piece(self.x_piece)
        self.o = not self.o


if __name__ == '__main__':
    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    board = [[None for _ in range(3)] for _ in range(3)]
    board_view = TicTacToeBoardView(window, board, scale[0], scale[1], reverse=True)
    pieces = {'bK': Piece('pieces/bK.svg', scale),
              'wN': Piece('pieces/wN.svg', scale),
              'bR': Piece('pieces/bR.svg', scale),
              'wK': Piece('pieces/wK.svg', scale)}
    board_view.squares[1][0].set_piece(pieces['bK'])
    board_view.squares[1][1].set_piece(pieces['wN'])
    # board_view.squares[6][5].set_piece(pieces['bR'])
    # board_view.squares[5][4].set_piece(pieces['wK'])

    board_view.pack()
    window.mainloop()
