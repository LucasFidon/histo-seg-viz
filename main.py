# This is a Python script for visualising histology tiles and pixel-wise segmentation.

from argparse import ArgumentParser
import numpy as np
from bokeh.layouts import column, row
from bokeh.io import output_file, show
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, CustomJS, Slider
from data.data_loader import load_data, SUPPORTED_EXTENSION
from data.color_template import CLASS2RGB

FIG_MAX_DIM = 600
ALPHA_INIT = 0.5

parser = ArgumentParser()
parser.add_argument(
    '--img',
    type=str,
    help='Image to display. Supported file extension: %s' % str(SUPPORTED_EXTENSION)
)
parser.add_argument(
    '--seg',
    type=str,
    help='Segmentation to display. Supported file extension: %s' % str(SUPPORTED_EXTENSION)
)


def convert_img_for_display(img):
    xdim, ydim, chan = img.shape
    # Convert the tile for display
    out = np.empty((xdim, ydim), dtype=np.uint32)
    view = out.view(dtype=np.uint8).reshape((xdim, ydim, 4))
    for i in range(xdim):
        for j in range(ydim):
            view[i, j, 0] = img[i, j, 0]
            view[i, j, 1] = img[i, j, 1]
            view[i, j, 2] = img[i, j, 2]
            if chan == 4:  # RGBA
                view[i, j, 3] = img[i, j, 3]
            else:
                view[i, j, 3] = 255
    # Reverse x axis to display the image correctly
    out = out[::-1, :]
    return out


def convert_seg_for_display(seg):
    xdim, ydim = seg.shape
    # Convert the segmentation for display
    overlay = np.empty((xdim, ydim), dtype=np.uint32)
    o_view = overlay.view(dtype=np.uint8).reshape((xdim, ydim, 4))
    for i in range(xdim):
        for j in range(ydim):
            color = CLASS2RGB[seg[i, j]]
            o_view[i, j, 0] = color[0]
            o_view[i, j, 1] = color[1]
            o_view[i, j, 2] = color[2]
            if seg[i, j] == 0:
                o_view[i, j, 3] = 0
            else:
                o_view[i, j, 3] = 255
    # Reverse x axis to display the image correctly
    overlay = overlay[::-1, :]
    return overlay


def main(args):
    # Load the tile to display as RGB image
    tile = load_data(args.img, seg=False)
    seg = load_data(args.seg, seg=True)
    xdim, ydim, chan = tile.shape

    # Convert the tile and the segmentation for display
    img = convert_img_for_display(tile)
    overlay = convert_seg_for_display(seg)

    # Make a data source for the main segmentation
    slider = Slider(title="Opacity", start=0, end=1, value=ALPHA_INIT, step=0.01)
    source = ColumnDataSource(
        data=dict(global_alpha=[ALPHA_INIT], image=[overlay])
    )

    # Display the image
    dim_ratio = FIG_MAX_DIM / max(xdim, ydim)
    width = int(dim_ratio * ydim)
    height = int(dim_ratio * xdim)
    p = figure(
        width=width, height=height, x_range=(0, ydim), y_range=(0, xdim),
        title="Image and Segmentation",
    )
    p.image_rgba(
        image=[img], x=0, y=0, dw=ydim, dh=xdim,
    )
    p.image_rgba(
        image='image', x=0, y=0, dw=ydim, dh=xdim,
        global_alpha='global_alpha', source=source,
    )

    # Define a callback to change dynamically the opacity of the segmentation
    # when the user interacts with the slider
    callback = CustomJS(
        args=dict(source=source, slider=slider),
        code="""
        const alpha = source.data["global_alpha"]
        alpha[0] = slider.value
        source.change.emit()
        """
    )
    slider.js_on_change('value', callback)

    output_file("image_and_segmentation.html")
    layout = column(p, slider)
    show(layout)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
