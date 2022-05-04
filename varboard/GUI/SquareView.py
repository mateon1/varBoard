import tkinter as tk
import tkinter.messagebox


class Square(tk.Frame):
    def __init__(self, master, board_view, height, width, image=None):
        def on_click(event):
            board_view.handle_square_btn(self)

        super().__init__(master=master, height=height, width=width, relief='sunken', borderwidth=1)
        self.piece = None
        self.lbl_image = tk.Label(master=self, image=image, bg='linen')
        self.lbl_image.bind('<Button-1>', on_click)
        if image:
            self.lbl_image.pack(expand=True, fill='both')
        self.bind('<Button-1>', on_click)

    def set_image(self, new_image):
        self.lbl_image.configure(image=new_image)
        self.lbl_image.pack(expand=True, fill='both')

    def set_piece(self, piece):
        self.piece = piece
        self.set_image(piece.pimg)

    def set_background(self, color):
        self.configure(bg=color)
        self.lbl_image.configure(bg=color)
