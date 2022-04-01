import tkinter as tk
from Square import Square
from PieceView import Piece


class BoardView(tk.Frame):
    def __init__(self, master, board, square_height, square_width, *args, reverse=False, **kwargs):
        kwargs['relief'] = kwargs.get('relief', 'raised')
        kwargs['bd'] = kwargs.get('bd', 10)
        super().__init__(master, *args, **kwargs)

        board_height = len(board)
        board_width = len(board[0])

        white_color = 'linen'
        black_color = 'saddle brown'

        if reverse:
            x_pack_side = tk.RIGHT
            y_pack_side = tk.BOTTOM
        else:
            x_pack_side = tk.LEFT
            y_pack_side = tk.TOP

        # frame for main board with squares in grid
        self.frm_main_board = tk.Frame(master=self, relief=tk.RAISED, bd=6)

        # frames for bars with numbers and letters
        frm_number_bar = tk.Frame(master=self)
        frm_letter_bar = tk.Frame(master=self)

        self.squares = [[Square(self.frm_main_board, square_height, square_width) for _ in range(board_width)]
                        for _ in range(board_height)]

        for row in range(board_height):
            # filling bar with numbers
            lbl_number = tk.Label(master=frm_number_bar, text=str(board_height - row))
            lbl_number.pack(expand=True, fill='y', side=y_pack_side)

            # filling bar with letters
            lbl_letter = tk.Label(master=frm_letter_bar, text=chr(ord('A') + row))
            lbl_letter.pack(expand=True, fill='x', side=x_pack_side)

            self.frm_main_board.columnconfigure(row, weight=1)
            self.frm_main_board.rowconfigure(row, weight=1)
            for column in range(board_width):
                padx, pady = (0, 0), (0, 0)
                # if row == 0: pady = (20, 0)
                # if column == board_width-1: padx = (0, 20)

                self.squares[row][column].grid(row=row, column=column, sticky='NESW', padx=padx, pady=pady)

                # setting color of squares
                color1, color2 = white_color, black_color
                if reverse:
                    color1, color2 = color2, color1

                if abs(row-column) % 2 == 0:
                    self.squares[row][column].set_background(color1)
                else:
                    self.squares[row][column].set_background(color2)

        self.frm_main_board.grid(row=1, column=1)
        frm_letter_bar.grid(row=2, column=1, sticky='nesw')
        frm_number_bar.grid(row=1, column=0, sticky='nesw')

        # empty bars for rest sides to maintain symmetry
        tk.Frame(master=self, height=10).grid(row=0, column=1)
        tk.Frame(master=self, width=10).grid(row=1, column=2)

        self.rowconfigure([0, 1], weight=1)
        self.columnconfigure([0, 1], weight=1)

    def set_square_image(self, row, column, pimg):
        self.squares[row][column].set_image(pimg)


if __name__ == '__main__':
    window = tk.Tk()
    window.aspect(1, 1, 1, 1)
    scale = (75, 75)
    board = [[None for _ in range(8)] for _ in range(8)]
    board_view = BoardView(window, board, scale[0], scale[1], reverse=False)
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
