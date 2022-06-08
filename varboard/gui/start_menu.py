import tkinter as tk
from typing import Any


class StartMenu(tk.Frame):
    def __init__(self, *args: Any, **kargs: Any):
        super().__init__(*args, **kargs)

        # title
        self.title_lbl = tk.Label(master=self, text="VarBoard")
        self.title_lbl.config(font=("Courier", 50))
        self.title_lbl.pack(side=tk.TOP)

        # variant frame
        self.variant_frm = tk.Frame(master=self)
        # # variant label
        self.variant_lbl = tk.Label(master=self.variant_frm, text="Variant")
        self.variant_lbl.config(font=("Courier", 12))
        self.variant_lbl.pack(side=tk.LEFT)
        # # variant OptionMenu
        self.variant_value_inside = tk.StringVar(self.variant_frm)
        self.variant_value_inside.set("Select a variant")
        self.variants = ["Standard", "No castling", "Pawns only", "Racing Kings", "TicTacToe"]
        self.variant_om = tk.OptionMenu(self.variant_frm, self.variant_value_inside, *self.variants)
        self.variant_om.config(font=("Courier", 12))
        self.variant_om.pack(anchor=tk.E)
        self.variant_frm.pack(anchor=tk.W, fill=tk.X)

        # Mode frame
        self.mode_frm = tk.Frame(master=self)
        # # variant label
        self.mode_lbl = tk.Label(master=self.mode_frm, text="Mode")
        self.mode_lbl.config(font=("Courier", 12))
        self.mode_lbl.pack(side=tk.LEFT)
        # # variant OptionMenu
        self.mode_value_inside = tk.StringVar(self.mode_frm)
        self.mode_value_inside.set("Select a mode")
        self.modes = ["2 Players", "Player vs Computer", "Computer vs Computer"]
        self.mode_om = tk.OptionMenu(self.mode_frm, self.mode_value_inside, *self.modes)
        self.mode_om.config(font=("Courier", 12))
        self.mode_om.pack(anchor=tk.E)
        self.mode_frm.pack(anchor=tk.W, fill=tk.X)

        # Time scale
        self.time_scale_frm = tk.Frame(master=self)
        # # variant label
        self.scale_lbl = tk.Label(master=self.time_scale_frm, text="Minutes per side")
        self.scale_lbl.config(font=("Courier", 12))
        self.scale_lbl.pack(side=tk.LEFT)
        # # scale
        var = tk.IntVar()
        def disp_val(val):
            var.set(f'Slider is at {self.scale.get()}')
        self.scale = tk.Scale(
            master=self.time_scale_frm,
            from_=0,
            to=60,
            orient=tk.HORIZONTAL,
            command=disp_val
        )
        self.scale.pack(side=tk.RIGHT, anchor=tk.E)
        self.time_scale_frm.pack(anchor=tk.W, fill=tk.X)


        # Increment scale
        self.increment_scale_frm = tk.Frame(master=self)
        # # variant label
        self.increment_lbl = tk.Label(master=self.increment_scale_frm, text="Increment in seconds")
        self.increment_lbl.config(font=("Courier", 12))
        self.increment_lbl.pack(side=tk.LEFT)
        # # scale
        increment_var = tk.IntVar()
        self.increment_scale = tk.Scale(
            master=self.increment_scale_frm,
            from_=0,
            to=60,
            orient=tk.HORIZONTAL,
            command=disp_val
        )
        self.increment_scale.pack(side=tk.RIGHT, anchor=tk.E)
        self.increment_scale_frm.pack(anchor=tk.W, fill=tk.X)

        def handle_play_btn() -> None:
            self.master.handle_play_btn(self.variant_value_inside.get(), self.mode_value_inside.get(),
                                        self.scale.get()*60, self.increment_scale.get()) # type: ignore

        self.play_btn = tk.Button(self, text="Play", font=("Courier", 12), command=handle_play_btn)
        self.play_btn.pack()


if __name__ == '__main__':
    root = tk.Tk()
    sm = StartMenu(master=root)
    sm.pack()
    root.mainloop()
