from __future__ import annotations

import io
import tkinter as tk
import tkinter.ttk as ttk
from math import ceil
from typing import Any, TYPE_CHECKING
from varboard.state import Color
from varboard.controller import GameController

import cairosvg
from PIL import Image, ImageTk

if TYPE_CHECKING:
    from .board_view import BoardView


class SquareView(tk.Frame):
    def __init__(self, master: Any, board_view: BoardView, height: int, width: int, x: int, y: int):
        super().__init__(master=master, height=height + 2, width=width + 2, relief='sunken', borderwidth=1)
        self.bind('<Button-1>', lambda event: board_view.handle_square_btn(self, x, y))

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

class AdvantageBar(ttk.Progressbar):
    def __init__(self, *args, **kwargs):
        kwargs['orient'] = 'vertical'
        kwargs['mode'] = 'determinate'
        kwargs['length'] = 280
        super(AdvantageBar, self).__init__(*args, **kwargs)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('white.Vertical.TProgressbar', background='white', troughcolor='black', bordercolor='lightgrey')
        self.white_advantage = 0.5
        self.configure(style='white.Vertical.TProgressbar')

    def set_advantages(self, white):
        self.white_advantage = white
        self.update()

    def update(self) -> None:
        if self['value'] < self.white_advantage*100:
            d = 0.5
        else:
            d = -0.5
        if abs(self['value'] - self.white_advantage*100) > 1:
            self.configure(value=self['value']+d)
            self.after(10, self.update)


class ChessTimer(ttk.Label):
    def __init__(self, *args, color: Color, controller: GameController, **kwargs):
        super().__init__(kwargs['master'])
        self.configure(font=('Courier', 25))
        self.active = False
        self.controller = controller
        self.time = 0
        if color == Color.WHITE:
            self.time_index = 0
        else:
            self.time_index = 1
        self.configure(text=f'{self.time_to_text(self.time)}')

    def start(self):
        self.active = True
        self.time = self.controller.tc.time[self.time_index]
        self.count_down()

    def count_down(self):
        if not self.active:
            return

        self.configure(text=f'{self.time_to_text(self.time)}')
        self.time -= 1
        self.after(1000, self.count_down)

    def stop(self):
        self.time = self.controller.tc.time[self.time_index]
        self.configure(text=f'{self.time_to_text(self.time)}')
        self.active = False

    @staticmethod
    def time_to_text(seconds):
        seconds = ceil(seconds)
        min_txt = str(seconds//60)
        if len(min_txt) < 2:
            min_txt = '0'+min_txt
        seconds = seconds % 60
        sec_txt = str(seconds)
        if seconds < 10:
            sec_txt = '0'+sec_txt
        return f'{min_txt}:{sec_txt}'

    def set_time(self, time):
        self.configure(text=f'{self.time_to_text(time)}')
        self.time = time
