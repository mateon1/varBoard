from __future__ import annotations

import io
import tkinter as tk
from typing import Any, TYPE_CHECKING

import cairosvg
from PIL import Image, ImageTk

if TYPE_CHECKING:
    from .board_view import BoardView


class SquareView(tk.Frame):
    def __init__(self, master: Any, board_view: BoardView, height: int, width: int, x: int, y: int):
        def on_click(event):
            board_view.handle_square_btn(self, x, y)

        super().__init__(master=master, height=height + 2, width=width + 2, relief='sunken', borderwidth=1)
        self.bind('<Button-1>', on_click)

    def set_color(self, color: str) -> None:
        self.configure(bg=color)


imagecache: dict[str, Image] = {}


class PieceView(tk.Label):
    @staticmethod
    def load_image(image_path: str, image_size: tuple[int, int]) -> Any:
        if image_path in imagecache:
            img = imagecache[image_path]
        else:
            img_data = cairosvg.svg2png(url=image_path, output_height=512, output_width=512)
            img = Image.open(io.BytesIO(img_data))
            img = img.resize(image_size, Image.ANTIALIAS)
            imagecache[image_path] = img
        return ImageTk.PhotoImage(img)

    def __init__(self, master: Any, board_view: BoardView, image: ImageTk.PhotoImage):
        super().__init__(master=master, image=image, bg='linen')
        self.x = -1
        self.y = -1
        self.pimg = image
        self.bind('<Button-1>', lambda event: board_view.handle_square_btn(self, self.x, self.y))

    def set_image(self, new_image: Any) -> None:
        self.configure(image=new_image)

    def set_color(self, color: str) -> None:
        self.configure(bg=color)

    def set_xy(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
