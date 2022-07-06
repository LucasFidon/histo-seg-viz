# This script is a data loader factory
import os
import nibabel as nib
import numpy as np
import imageio
import openslide

SUPPORTED_EXTENSION = [
    '.nii',
    '.nii.gz',
    '.png',
]


def _get_extension(path):
    file_name = os.path.split(path)[1]
    ext_list = file_name.split('.')[1:]
    ext = ''
    for n in ext_list:
        ext += '.' + n
    assert ext in SUPPORTED_EXTENSION, \
        "Found extension %s that is not supported for %s" % (ext, path)
    return ext


def _load_png(path, seg):
    data = imageio.imread(path).astype(np.uint32)
    return data


def _load_nii(path, seg):
    data_nib = nib.load(path)
    data = data_nib.get_fdata()
    # Transpose the image or segmentation
    data = np.transpose(data, axes=(1, 0, 2))
    if seg:
        data = data.astype(np.uint8)
        if data.ndim == 3:
            data = data[:, :, 0]
    else:
        data = 255. * data
        data = data.astype(np.uint32)
    return data


def _load_tiff(path):
    # TODO: read_region
    tile = openslide.open_slide(path).read_region((0, 0), 0, (224, 224))
    tile = np.asarray(tile)
    alpha = tile[:, :, -1]
    n_zeros = np.sum(alpha == 0)
    assert n_zeros == 0, 'Zero values found in alpha channel'
    tile = tile[:, :, :3] * (255. / alpha[:, :, None])
    return tile


def load_data(data_path, seg=False):
    ext = _get_extension(data_path)
    if ext == '.nii' or ext == '.nii.gz':
        data = _load_nii(data_path, seg)
    elif ext == '.png':
        data = _load_png(data_path, seg)
    else:
        raise IOError('Could not load %s' % data_path)
    return data
