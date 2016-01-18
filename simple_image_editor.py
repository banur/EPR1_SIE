""" simple imgage editor

"""

from tkinter import *
import io
import numpy as np
import scipy
from scipy import ndimage
from PIL import Image, ImageTk, ImageOps
import tkinter.filedialog
from skimage import io as ski_io
from skimage import filters as ski_filters
from skimage import data, img_as_float
from skimage import exposure, color


__author__ = "6224961: Marie-Luise Katzer, 6192860: Georg Schuhardt"
__copyright__ = "Copyright 2015/2016 – EPR-Goethe-Uni"
__credits__ = "nothing"
__email__ = "georg.schuhardt@gmail.com"
__github__ = "https://github.com/banur/EPR1_SIE"

class SIE(Frame):
    """  """

    undo_stack = {}
    redo_stack = {}
    pic = None
    pic_array = None
    # canvas = None

    def __init__(self, master=None):
        Frame.__init__(self, master, relief=SUNKEN, bd=2)

        self.create_menubar(master)

    def create_menubar(self, master):
        """ Create the menu. """
        menubar = Menu(self.master)
        self.menubar = Menu(self)

        # File menu
        file_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        recent_menu = Menu(self, tearoff=0)
        # file_menu.add_cascade(label="Open Recent", menu=recent_menu)
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
        trans_menu.add_command(label="Contrast", command=self.on_contrast)
        trans_menu.add_command(label="Histogram", command=self.on_histogram)

        # Filter menu
        filter_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Filters", menu=filter_menu)
        edge_menu = Menu(self, tearoff=0)
        filter_menu.add_cascade(label="Edge", menu=edge_menu)
        edge_menu.add_command(label="Sobel", command=self.on_sobel)
        edge_menu.add_command(label="Prewitt", command=self.on_prewitt)
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

            self.pic = ImageTk.PhotoImage(file=file_name)
            self.canvas.image = self.pic
            width = self.undo_stack[num_images - 1].size[0]
            height = self.undo_stack[num_images - 1].size[1]
            self.canvas.config(width=width, height=height)
            self.canvas.create_image(0, 0, image=self.pic, anchor=NW)
            self.canvas.pack()

    def on_save(self):
        """ Show file explorer and save file. """
        num_images = len(self.undo_stack)
        save_dialog = tkinter.filedialog.asksaveasfilename(defaultextension=".png")
        if save_dialog is "":
            return
        else:
            self.undo_stack[num_images - 1].save(save_dialog, 'PNG')

    def show_pic(self):
        """ Update the canvas to display the image. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.pic = ImageTk.PhotoImage(image)
        self.canvas.image = self.pic
        width = self.undo_stack[num_images - 1].size[0]
        height = self.undo_stack[num_images - 1].size[1]
        if height < 400:
            height = 400
        if width < 400:
            width = 400
        self.canvas.config(width=width, height=height)
        self.canvas.create_image(0, 0, image=self.pic, anchor=NW)
        self.canvas.pack()

    def on_undo(self):
        """ Revert last change. """
        num_images = len(self.undo_stack)
        num_redo = len(self.redo_stack)
        if len(self.undo_stack) > 1:
            self.redo_stack[num_redo] = self.undo_stack.pop(num_images-1)
        self.show_pic()

    def on_redo(self):
        """ Redo the last reverted change. """
        num_images = len(self.undo_stack)
        num_redo = len(self.redo_stack)
        if len(self.redo_stack):
            self.undo_stack[num_images] = self.redo_stack.pop(num_redo-1)
        self.show_pic()

    def on_invert(self):
        """ Invert the image colours. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.undo_stack[num_images] = ImageOps.invert(image)
        self.redo_stack = {}
        self.show_pic()

    def on_grey(self):
        """ Transform the image to greyscale """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.undo_stack[num_images] = ImageOps.grayscale(image)
        self.redo_stack = {}
        self.show_pic()

    def on_threshold(self):
        """ Show threshold options and apply threshold to the image."""
        print("not implemented")
        # num_images = len(self.undo_stack)
        # image = np.asarray(self.undo_stack[num_images -1 ])
        # self.redo_stack = {}
        # self.show_pic()

    def on_scale(self):
        """ Show scaling options and scale the image. """
        num_images = len(self.undo_stack)
        image = self.undo_stack[num_images - 1]
        self.w = Popup(self.master, text="Scaling percent")
        self.wait_window(self.w.top)
        scale = float(self.w.value)/100
        width = int((float(image.size[0]) * float(scale)))
        height = int((float(image.size[1]) * float(scale)))
        self.undo_stack[num_images] = image.resize((width, height),
            Image.ANTIALIAS)
        self.redo_stack = {}
        self.show_pic()

    def on_fourier(self):
        """ Calculate the Fourier transformation. """
        num_images = len(self.undo_stack)
        image = np.asarray(self.undo_stack[num_images - 1])
        fourier = scipy.ndimage.fourier.fourier_uniform(image, size=1)
        self.undo_stack[num_images] = Image.fromarray(fourier)
        self.redo_stack = {}
        self.show_pic()

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
        self.show_pic()

    def on_contrast(self):
        """ Normalise the image. """
        num_images = len(self.undo_stack)
        image = np.asarray(self.undo_stack[num_images - 1])
        self.w = Popup(self.master, text="Cutoff value")
        self.wait_window(self.w.top)
        cutoff = int(self.w.value)
        p0, p100 = np.percentile(image, (cutoff, 100-cutoff))
        contrast = exposure.rescale_intensity(image, in_range=(p0, p100))
        self.undo_stack[num_images] = Image.fromarray(contrast)
        self.redo_stack = {}
        self.show_pic()

    def on_histogram(self):
        """ Show histogramme options and calculate the histogram."""
        num_images = len(self.undo_stack)
        image = np.asarray(self.undo_stack[num_images - 1])
        if len(image.shape) > 2:
            pic_array = image[:, :, 0]
        else:
            pic_array = image
        print(ndimage.measurements.histogram(pic_array, pic_array.min(), pic_array.max(), 2))
        self.redo_stack = {}
        self.show_pic()

    def on_sobel(self):
        """ Perfom the Sobel edge filter. """
        num_images = len(self.undo_stack)
        image = np.asarray(self.undo_stack[num_images - 1])
        if len(image.shape) > 2:
            pic_array = image[:, :, 0]
        else:
            pic_array = image
        p2, p98 = np.percentile(pic_array, (47, 53))
        pic_array = exposure.rescale_intensity(pic_array, in_range=(p2, p98))
        sobel = scipy.ndimage.filters.sobel(pic_array)
        self.undo_stack[num_images] = Image.fromarray(sobel)
        self.redo_stack = {}
        self.show_pic()

    def on_prewitt(self):
        """ Perform the Prewitt edge filter. """
        num_images = len(self.undo_stack)
        image = np.asarray(self.undo_stack[num_images - 1])
        if len(image.shape) > 2:
            pic_array = image[:, :, 0]
        else:
            pic_array = image
        p2, p98 = np.percentile(pic_array, (47, 53))
        pic_array = exposure.rescale_intensity(pic_array, in_range=(p2, p98))
        prewitt = scipy.ndimage.filters.prewitt(pic_array)
        self.undo_stack[num_images] = Image.fromarray(prewitt)
        self.redo_stack = {}
        self.show_pic()

    def on_smooth1(self):
        """ Perform the XXXXXXX smoothing filter. """
        print("not implemented")
        # num_images = len(self.undo_stack)
        # image = np.asarray(self.undo_stack[num_images -1 ])
        # self.redo_stack = {}
        # self.show_pic()

    def on_smooth2(self):
        """ Perform the XXXXXXX smoothing filter. """
        print("not implemented")
        # num_images = len(self.undo_stack)
        # image = np.asarray(self.undo_stack[num_images -1 ])
        # self.redo_stack = {}
        # self.show_pic()


class Popup():
    """ Display entry field popups. """

    def __init__(self, master, text):
        top = self.top = Toplevel(master)
        self.label = Label(top, text=text)
        self.label.pack()
        self.entry = Entry(top)
        self.entry.pack()
        self.button = Button(top, text='Ok', command=self.cleanup)
        self.button.pack()

    def cleanup(self):
        """ Destroy the popup and return the entry field value. """
        self.value = self.entry.get()
        self.top.destroy()

    def popup1(self):
        self.w = popupWindow(self.master)
        self.master.wait_window(self.w.top)

    def entryValue(self):
        return self.w.value

def main():
    """ Start the programme. """
    root = Tk()
    run = SIE(root)
    root.mainloop()


if __name__ == '__main__':
    main()
