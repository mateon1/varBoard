import tkinter as tk


class StartMenu(tk.Frame):
    def __init__(self, *args, **kargs):
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
        self.variants = ["Standard", "TicTacToe"]
        self.variant_om = tk.OptionMenu(self.variant_frm, self.variant_value_inside, *self.variants)
        self.variant_om.config(font=("Courier", 12))
        self.variant_om.pack()
        self.variant_frm.pack()

        # Mode frame
        self.mode_frm = tk.Frame(master=self)
        # # variant label
        self.mode_lbl = tk.Label(master=self.mode_frm, text="Mode")
        self.mode_lbl.config(font=("Courier", 12))
        self.mode_lbl.pack(side=tk.LEFT)
        # # variant OptionMenu
        self.mode_value_inside = tk.StringVar(self.mode_frm)
        self.mode_value_inside.set("Select a mode")
        self.modes = ["2 players", "Player vs Computer", "Computer vs Computer"]
        self.mode_om = tk.OptionMenu(self.mode_frm, self.mode_value_inside, *self.modes)
        self.mode_om.config(font=("Courier", 12))
        self.mode_om.pack(side=tk.LEFT, fill='x')
        self.mode_frm.pack()

        def handle_play_btn():
            self.master.handle_play_btn(self.variant_value_inside.get())

        self.play_btn = tk.Button(self, text="Play", font=("Courier", 12), command=handle_play_btn)
        self.play_btn.pack()


if __name__ == '__main__':
    root = tk.Tk()
    sm = StartMenu(master=root)
    sm.pack()
    root.mainloop()