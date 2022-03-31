import cairosvg
from PIL import Image, ImageTk
import io


class Piece:
    def __init__(self, image_path, image_size):
        img_data = cairosvg.svg2png(url=image_path, output_height=2048, output_width=2048)
        img = Image.open(io.BytesIO(img_data))
        img = img.resize(image_size, Image.ANTIALIAS)
        self.pimg = ImageTk.PhotoImage(img)
