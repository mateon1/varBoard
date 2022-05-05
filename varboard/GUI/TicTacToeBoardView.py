from .BoardView import *


class TicTacToeBoardView(BoardView):
    def __init__(self, master, controller, square_scale, reverse=False, white_color='white', black_color='white', *args, **kwargs):
        super().__init__(master, controller, square_scale, reverse, white_color, black_color, *args, **kwargs)

    def grid_components(self):
        self.frm_main_board.grid(row=0, column=0)

    def handle_square_btn(self, square, x, y):
        print("TODO: Ask self.controller whether it's a legal move, and make it")

if __name__ == '__main__':
    from .. import variant
    from ..controller import GameController
    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    controller = GameController(variant.TicTacToe(), None)
    board_view = TicTacToeBoardView(window, controller, scale, reverse=False)
    print(board_view.tk)
    board_view.set_piece(1, 1, 'o')
    board_view.set_piece(0, 1, 'x')
    board_view.set_piece(2, 0, 'o')

    board_view.pack()
    window.mainloop()
