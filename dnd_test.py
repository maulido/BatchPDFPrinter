import customtkinter as ctk
from tkinterdnd2 import TkinterDnD, DND_FILES

class TkinterDnD_CTk(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

app = TkinterDnD_CTk()
app.geometry("400x300")
app.title("DND Test")

def drop(event):
    print("Dropped:", event.data)
    app.destroy()

app.drop_target_register(DND_FILES)
app.dnd_bind('<<Drop>>', drop)
print("Ready")
app.after(1000, lambda: app.destroy())
app.mainloop()
