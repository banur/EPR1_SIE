""" simple imgage editor

"""

from tkinter import *
import io
import numpy
import scipy
from scipy import ndimage
from PIL import Image, ImageTk, ImageOps
import tkinter.filedialog
from skimage import io as ski_io
from skimage import filters as ski_filters
from skimage import img_as_ubyte
from skimage.color.adapt_rgb import adapt_rgb, each_channel


class SIE(Frame):
    """  """

    undo_stack = {}
    redo_stack = {}
    pic = None
    pic_array = None

    def __init__(self, master=None):
        Frame.__init__(self, master, relief=SUNKEN, bd=2)

        self.create_menubar(master)

    def create_menubar(self, master):
        """ Create the menu. """
        menubar = Menu(self.master)
        self.menubar = Menu(self)

#        for name in ("file1.txt", "file2.txt", "file3.txt"):
#            recentMenu.add_command(label=name)

        # File menu
        file_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        recent_menu = Menu(self, tearoff=0)
        file_menu.add_cascade(label="Open Recent", menu=recent_menu)

        file_menu.add_command(label="Open", command=self.on_open)
        file_menu.add_command(label="Save", command=self.on_save)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)

        # Edit menu
        edit_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.on_undo)
        edit_menu.add_command(label="Redo", command=self.on_redo)

        # Colour menu
        colour_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Colour", menu=colour_menu)
        colour_menu.add_command(label="Invert", command=self.on_invert)
        colour_menu.add_command(label="Grey Scale", command=self.on_grey)
        colour_menu.add_command(label="Threshold", command=self.on_threshold)

        # Transform menu
        trans_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Transform", menu=trans_menu)
        trans_menu.add_command(label="Scale", command=self.on_scale)
        trans_menu.add_command(label="Fourier", command=self.on_fourier)
        flip_menu = Menu(self, tearoff=0)
        trans_menu.add_cascade(label="Flip", menu=flip_menu)
        flip_menu.add_command(label="vertical", command=lambda:
                              self.on_flip("v"))
        flip_menu.add_command(label="horizontal", command=lambda:
                              self.on_flip("h"))
        trans_menu.add_command(label="Normalise", command=self.on_normalise)
        trans_menu.add_command(label="Histogram", command=self.on_histogram)

        # Filter menu
        filter_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Filters", menu=filter_menu)
        edge_menu = Menu(self, tearoff=0)
        filter_menu.add_cascade(label="Edge", menu=edge_menu)
        edge_menu.add_command(label="Scharr", command=self.on_scharr)
        edge_menu.add_command(label="Sobel", command=self.on_sobel)
        edge_menu.add_command(label="Prewitt", command=self.on_prewitt)
        edge_menu.add_command(label="Roberts", command=self.on_roberts)
        smooth_menu = Menu(self, tearoff=0)
        filter_menu.add_cascade(label="Smoothing", menu=smooth_menu)
        smooth_menu.add_command(label="Smooth 1", command=self.on_smooth1)
        smooth_menu.add_command(label="Smooth 1", command=self.on_smooth2)

        self.master.config(menu=menubar)

        try:
            self.master.config(menu=self.menubar)
        except AttributeError:
            # master is a toplevel window (Python 1.4/Tkinter 1.63)
            self.master.tk.call(master, "config", "-menu", self.menubar)
        self.master.title("Simple Image Editor")
        self.pack(fill=BOTH, expand=1)
        self.canvas = Canvas(self, bg="white", width=400, height=400,
                             bd=0, highlightthickness=0)
        self.canvas.pack()
        self.master = master

    def on_open(self):
        """ Show file explorer and load image file. """
        filetypes = [('PNG', '*.png'),
                     ('JPG', '*.jpg'),
                     ('BMP', '*.bmp'),
                     ('TIFF', '*.tiff')]
        open_dialog = tkinter.filedialog.Open(self, filetypes=filetypes)
        file_name = open_dialog.show()

        if file_name != '':
            self.undo_stack = {}
            self.undo_stack[0] = Image.open(file_name)
            num_images = len(self.undo_stack)
            self.undo_stack[num_images - 1].show()
            print(self.undo_stack[num_images - 1])
            self.pic_array = ski_io.imread(file_name)
            print(type(self.pic_array))


            self.pic = PhotoImage(file_name)
            label = Label(self.master, image=self.pic)
            label.image = self.pic  # to keep the reference for the image.
            label.configure(image=self.pic)
            label.pack()  # <--- pack

    def on_save(self):
        """ Show file explorer and save file. """
        num_images = len(self.undo_stack)
        save_dialog = tkinter.filedialog.asksaveasfilename(defaultextension=".png")
        if save_dialog is None:
            return
        else:
            self.undo_stack[num_images - 1].save(save_dialog, 'JPEG')

    def on_undo(self):
        """ Revert last change. """
        num_images = len(self.undo_stack)
        num_redo = len(self.redo_stack)
        if len(self.undo_stack) > 1:
            self.redo_stack[num_redo] = self.undo_stack.pop(num_images-1)
            self.undo_stack[num_images - 2].show()

    def on_redo(self):
        """ Redo the last reverted change. """
        num_images = len(self.undo_stack)
        num_redo = len(self.redo_stack)
        if len(self.redo_stack):
            self.undo_stack[num_images] = self.redo_stack.pop(num_redo-1)
            self.undo_stack[num_images - 1].show()

    def on_invert(self):
        """ Invert the image colours. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.undo_stack[num_images] = ImageOps.invert(image)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_grey(self):
        """ Transform the image to greyscale """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.undo_stack[num_images] = ImageOps.grayscale(image)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_threshold(self):
        """ Show threshold options and threshold the image."""
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]

        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_scale(self):
        """ Show scaling options and scale the image. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        scale = 0.5
        width = int((float(image.size[0]) * float(scale)))
        height = int((float(image.size[1]) * float(scale)))
        self.undo_stack[num_images] = image.resize((width, height),
            Image.ANTIALIAS)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_fourier(self):
        """ Calculate the Fourier transformation. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]

        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_flip(self, direction):
        """ Flip the image in the direction. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        # vertical
        if direction == "v":
            self.undo_stack[num_images] = ImageOps.flip(image)
        # horizontal
        if direction == "h":
            self.undo_stack[num_images] = ImageOps.mirror(image)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_normalise(self):
        """ Normalise the image. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.undo_stack[num_images] = ImageOps.autocontrast(image, cutoff=0.5)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_histogram(self):
        """ Show histogramme options and calculate the histogram."""
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]

        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_sobel(self):
        """ Perfom the Sobel edge filter.  """
        num_images = len(self.undo_stack)
        sobel = ski_filters.sobel(self.pic_array[:, :, 0])
        self.undo_stack[num_images] = Image.fromarray(sobel)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_scharr(self):
        """ Perform the Scharr edge filter. """
        num_images = len(self.undo_stack)
        scharr = ski_filters.scharr(self.pic_array[:, :, 0])
        self.undo_stack[num_images] = Image.fromarray(scharr)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_prewitt(self):
        """ Perform the Prewitt edge filter. """
        num_images = len(self.undo_stack)
        prewitt = ski_filters.prewitt(self.pic_array[:, :, 0])
        self.undo_stack[num_images] = Image.fromarray(prewitt)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_roberts(self):
        """ Perform the Roberts edge filter. """
        num_images = len(self.undo_stack)
        roberts = ski_filters.roberts(self.pic_array[:, :, 0])
        self.undo_stack[num_images] = Image.fromarray(roberts)
        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_smooth1(self):
        """ Show options for XXXXXX and """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]

        self.redo_stack = {}
        self.undo_stack[num_images].show()

    def on_smooth2(self):
        """ Show options for XXXXXX and """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images -1 ]

        self.redo_stack = {}
        self.undo_stack[num_images].show()


def main():
    """ Start the programme. """
    root = Tk()
    run = SIE(root)
    root.mainloop()


if __name__ == '__main__':
    main()
