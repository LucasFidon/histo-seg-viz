# This is a Python script for visualising histology tiles and pixel-wise segmentation.

from argparse import ArgumentParser
import numpy as np
from bokeh.io import output_file, show
from bokeh.plotting import curdoc, figure
from data.data_loader import load_data, SUPPORTED_EXTENSION

FIG_MAX_DIM = 600

parser = ArgumentParser()
parser.add_argument(
    '--img',
    type=str,
    help='Image to display. Supported file extension: %s' % str(SUPPORTED_EXTENSION)
)


def main(args):
    # Load the tile to display as RGB image
    tile = load_data(args.img, seg=False)
    xdim, ydim, chan = tile.shape

    # Convert the tile for display
    img = np.empty((xdim, ydim), dtype=np.uint32)
    view = img.view(dtype=np.uint8).reshape((xdim, ydim, 4))
    for i in range(xdim):
        for j in range(ydim):
            view[i, j, 0] = tile[i, j, 0]
            view[i, j, 1] = tile[i, j, 1]
            view[i, j, 2] = tile[i, j, 2]
            if chan == 4:  # RGBA
                view[i, j, 3] = tile[i, j, 3]
            else:
                view[i, j, 3] = 255
    # Reverse x axis to display the image correctly
    img = img[::-1, :]

    # Display the image
    dim_ratio = FIG_MAX_DIM / max(xdim, ydim)
    width = int(dim_ratio * ydim)
    height = int(dim_ratio * xdim)
    p = figure(width=width, height=height, x_range=(0, ydim), y_range=(0, xdim))
    p.image_rgba(image=[img], x=[0], y=[0], dw=[ydim], dh=[xdim])

    output_file("image_and_segmentation.html")

    show(p)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
