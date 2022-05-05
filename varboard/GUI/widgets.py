import tkinter as tk
import tkinter.messagebox
import cairosvg
import io
from PIL import Image, ImageTk
from typing import Any

class SquareView(tk.Frame):
    def __init__(self, master, board_view, height, width, x, y):
        def on_click(event):
            board_view.handle_square_btn(self, x, y)

        super().__init__(master=master, height=height, width=width, relief='sunken', borderwidth=1)
        self.bind('<Button-1>', on_click)

    def set_color(self, color: str) -> None:
        self.configure(bg=color)


class PieceView(tk.Label):
    @staticmethod
    def load_image(image_path: str, image_size: tuple[int, int]) -> Any:
        img_data = cairosvg.svg2png(url=image_path, output_height=2048, output_width=2048)
        img = Image.open(io.BytesIO(img_data))
        img = img.resize(image_size, Image.ANTIALIAS)
        return ImageTk.PhotoImage(img)

    def __init__(self, master, image: Any):
        super().__init__(master=master, image=image, bg='linen')
        self.pimg = image

    def set_image(self, new_image: Any) -> None:
        self.configure(image=new_image)

    def set_color(self, color: str) -> None:
        self.configure(bg=color)
