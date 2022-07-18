# This is a Python script for visualising an histology tiles and one or several pixel-wise segmentations.

import os
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
CLASS_NAMES = {
    1: 'Normal',
    2: 'Stroma',
    3: 'Tumor',
}

parser = ArgumentParser()
parser.add_argument(
    '-i',
    '--img',
    type=str,
    help='Path to the image to display. Supported file extension: %s' % str(SUPPORTED_EXTENSION)
)
parser.add_argument(
    '-s',
    '--seg',
    type=str,
    nargs='+',
    help='Path to the segmentation(s) to display. Several paths can be given separated by a space.'
         ' Supported file extension: %s' % str(SUPPORTED_EXTENSION),
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


def short_path_to_display(path):
    dir_n, file_n = os.path.split(path)
    out = os.path.split(dir_n)[1] + '/' + file_n
    return out


def main(args):
    # Load the tile to display as RGB image
    tile = load_data(args.img, seg=False)
    img_name = short_path_to_display(args.img)
    xdim, ydim, chan = tile.shape

    # Convert the tile and the segmentation for display
    img = convert_img_for_display(tile)

    # Display options
    dim_ratio = FIG_MAX_DIM / max(xdim, ydim)
    width = int(dim_ratio * ydim)
    height = int(dim_ratio * xdim)

    # Create the figure
    sliders = {}
    sources = {}
    callbacks = {}
    figs = {}
    columns = []
    for seg_path in args.seg:
        # Load the segmentation
        seg = load_data(seg_path, seg=True)
        seg_name = short_path_to_display(seg_path)

        assert seg.shape[0] == xdim and seg.shape[1] == ydim, \
            "Segmentation %s dimension (%d, %d) do not match with image dimension (%d, %d)" % \
            (seg_path, seg.shape[0], seg.shape[1], xdim, ydim)
        overlay = convert_seg_for_display(seg)

        # Make a slider and a data source for the segmentation
        sliders[seg_path] = Slider(title="Opacity", start=0, end=1, value=ALPHA_INIT, step=0.01)
        sources[seg_path] = ColumnDataSource(
            data=dict(global_alpha=[ALPHA_INIT], image=[overlay])
        )

        # Create the figure and display the image and the segmentation
        figs[seg_path] = figure(
            width=width, height=height, x_range=(0, ydim), y_range=(0, xdim),
            title="Image (%s) Segmentation (%s)" % (img_name, seg_name),
        )
        figs[seg_path].image_rgba(
            image=[img], x=0, y=0, dw=ydim, dh=xdim,
        )

        figs[seg_path].image_rgba(
            image='image', x=0, y=0, dw=ydim, dh=xdim,
            global_alpha='global_alpha', source=sources[seg_path],
        )

        # Define a callback to change dynamically the opacity of the segmentation
        # when the user interacts with the slider
        callbacks[seg_path] = CustomJS(
            args=dict(source=sources[seg_path], slider=sliders[seg_path]),
            code="""
            const alpha = source.data["global_alpha"]
            alpha[0] = slider.value
            source.change.emit()
            """
        )
        sliders[seg_path].js_on_change('value', callbacks[seg_path])

        # Add class legend
        row_legend = []
        w = width
        h = FIG_MAX_DIM // 8
        legend = figure(
            width=w, height=h, x_range=(0, w), y_range=(0, h),
            title='Classes',
        )
        legend.xgrid.grid_line_color = None
        legend.ygrid.grid_line_color = None
        legend.xaxis.visible = False
        legend.yaxis.visible = False
        for i in range(1, 4):
            color = '#%02x%02x%02x' % (CLASS2RGB[i][0], CLASS2RGB[i][1], CLASS2RGB[i][2])
            color_text = 'white' if (CLASS2RGB[i][0] > 200 or CLASS2RGB[i][2] > 200) else 'black'
            x_center = int((i - 1 + 0.5) * w // 3)
            y_center = h // 2
            margin = 10
            legend.rect(
                x_center, y_center, width=w//3 - margin, height=h,
                fill_color=color, line_color='black', alpha=0.8,
            )
            legend.text(
                x_center, y_center - h//4, text=[CLASS_NAMES[i]], color=color_text,
                text_align='center',
            )

        columns.append(column(figs[seg_path], sliders[seg_path], legend))

    output_file("image_and_segmentation.html")
    # layout = column(p, slider)
    layout = row(columns)
    show(layout)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
