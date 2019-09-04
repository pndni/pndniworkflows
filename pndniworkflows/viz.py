import numpy as np
import nibabel
from matplotlib import figure
from matplotlib import gridspec
from matplotlib import style
from matplotlib.backends.backend_svg import FigureCanvasSVG
from io import StringIO
import jinja2
import re
import csv
from collections import defaultdict


ORIENTATION = [[2, 1],
               [1, 1],
               [0, 1]]
INDIVIDUAL_IMAGE_HEIGHT = 1.5
PLOTSIZE = 5, 4


# https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/_cm.py
COLORLIST = (
    (0.89411764705882357, 0.10196078431372549, 0.10980392156862745),
    (0.21568627450980393, 0.49411764705882355, 0.72156862745098038),
    (0.30196078431372547, 0.68627450980392157, 0.29019607843137257),
    (0.59607843137254901, 0.30588235294117649, 0.63921568627450975),
    (1.0,                 0.49803921568627452, 0.0),
    (1.0,                 1.0,                 0.2),
    (0.65098039215686276, 0.33725490196078434, 0.15686274509803921),
    (0.96862745098039216, 0.50588235294117645, 0.74901960784313726),
    (0.6,                 0.6,                 0.6),
    (0.4,                 0.76078431372549016, 0.6470588235294118),
    (0.9882352941176471,  0.55294117647058827, 0.3843137254901961),
    (0.55294117647058827, 0.62745098039215685, 0.79607843137254897),
    (0.90588235294117647, 0.54117647058823526, 0.76470588235294112),
    (0.65098039215686276, 0.84705882352941175, 0.32941176470588235),
    (1.0,                 0.85098039215686272, 0.18431372549019609),
    (0.89803921568627454, 0.7686274509803922,  0.58039215686274515),
    (0.70196078431372544, 0.70196078431372544, 0.70196078431372544),
    (0.55294117647058827, 0.82745098039215681, 0.7803921568627451),
    (1.0,                 1.0,                 0.70196078431372544),
    (0.74509803921568629, 0.72941176470588232, 0.85490196078431369),
    (0.98431372549019602, 0.50196078431372548, 0.44705882352941179),
    (0.50196078431372548, 0.69411764705882351, 0.82745098039215681),
    (0.99215686274509807, 0.70588235294117652, 0.3843137254901961),
    (0.70196078431372544, 0.87058823529411766, 0.41176470588235292),
    (0.9882352941176471,  0.80392156862745101, 0.89803921568627454),
    (0.85098039215686272, 0.85098039215686272, 0.85098039215686272),
    (0.73725490196078436, 0.50196078431372548, 0.74117647058823533),
    (0.8,                 0.92156862745098034, 0.77254901960784317),
    (1.0,                 0.92941176470588238, 0.43529411764705883))


def _load_and_orient(fname):
    x = nibabel.load(fname)
    orn = nibabel.orientations.io_orientation(x.affine)
    difforn = nibabel.orientations.ornt_transform(orn, ORIENTATION)
    y = x.as_reoriented(difforn)
    assert nibabel.orientations.aff2axcodes(y.affine) == ('S', 'A', 'R')
    return y


def _calcslices(s, nslices):
    step = (s - 1) // (nslices - 1)
    last = (nslices - 1) * step
    offset = (s - last - 1) // 2
    last += offset
    start = offset
    return list(range(start, last + 1, step))


def _get_vlims(x):
    vals = np.sort(x.ravel())
    ind = int(0.99 * len(vals))
    return 0.0, vals[ind]


def _imshow(imgfile, nslices, labelfile=None):
    svg = StringIO()
    img = _load_and_orient(imgfile)
    if labelfile is not None:
        label = _load_and_orient(labelfile)
        labelvals = list(np.unique(np.asarray(label.dataobj)))
        if 0 in labelvals:
            labelvals.pop(labelvals.index(0))
        if len(labelvals) > len(COLORLIST):
            raise RuntimeError('Not enough defined colors for label image')
    with style.context({'image.origin': 'lower',
                        'image.cmap': 'Greys_r',
                        'savefig.dpi': 300,
                        'axes.facecolor': 'black',
                        'figure.facecolor': 'black'}):
        fig = figure.Figure(figsize=(nslices * INDIVIDUAL_IMAGE_HEIGHT, 3 * INDIVIDUAL_IMAGE_HEIGHT))
        gs = gridspec.GridSpec(3, nslices, figure=fig, hspace=0.05, wspace=0.05, left=0, right=1, top=1, bottom=0)
        vmin, vmax = _get_vlims(img.get_fdata())
        pitch = np.sqrt(np.sum(img.affine[:3, :3] ** 2.0, axis=0))
        for rowind, ind in enumerate([2, 0, 1]):
            slice_locations = _calcslices(img.shape[ind], nslices)
            pitchtmp = list(pitch.copy())
            pitchtmp.pop(ind)
            aspect = pitchtmp[0] / pitchtmp[1]
            for colind, sl in enumerate(slice_locations):
                slicespec = tuple(slice(sl, sl + 1) if i == ind else slice(None) for i in range(3))
                imgslice = np.squeeze(np.asarray(img.slicer[slicespec].dataobj))
                ax = fig.add_subplot(gs[rowind, colind])
                ax.imshow(imgslice, vmin=vmin, vmax=vmax, aspect=aspect)
                ax.set_xticks([])
                ax.set_yticks([])
                if labelfile is not None:
                    labeldata = np.squeeze(np.asarray(label.slicer[slicespec].dataobj))
                    for lvind, lv in enumerate(labelvals):
                        ax.contour(labeldata == lv, levels=[0.5], colors=[COLORLIST[lvind]], linewidths=[0.5])
    FigureCanvasSVG(fig).print_svg(svg)
    svg.seek(0)
    return svg.read()


def _set_svg_class(svgstr, classname):
    return re.sub('<svg([^>]*)>', lambda m: '<svg{} class="{}">'.format(m.group(1), classname), svgstr, count=1)


def _dump(filename, str_):
    with open(filename, 'w') as f:
        f.write(str_)


def _load(filename):
    with open(filename, 'r') as f:
        return f.read()


def _load_template(template):
    env = jinja2.Environment(loader=jinja2.PackageLoader('pndniworkflows', 'templates'))
    return env.get_template(template)


def _render(out_file, template, data):
    template = _load_template(template)
    rend = template.render(data)
    _dump(out_file, rend)


def _single_opt_contours(name, image, out_file, nslices=7, label=None, form=True):
    svgstr = _imshow(image, nslices, labelfile=label)
    _render(out_file, 'single.tpl', {'name': name, 'svg': svgstr, 'form': form, 'name_no_spaces': name.replace(' ', '_')})


def single(name, image, out_file, nslices=7, form=True):
    """Write an html file to :py:obj:`out_file` showing the :py:obj:`image`
    with :py:obj:`nslices` slices in all three axial planes

    :param name: Name describing :py:obj:`image`
    :type name: str
    :param image: Image file name to show (readable by :py:mod:`nibabel`)
    :type image: str
    :param out_file: File name
    :type out_file: path-like object
    :param nslices: Number of slices to show in each plane
    :type nslices: int
    :param form: Include a QC form in the output
    :type form: bool
    """
    _single_opt_contours(name, image, out_file, nslices=nslices, form=form)


def compare(name1, image1, name2, image2, out_file, nslices=7, form=True):
    """Write an html file to :py:obj:`out_file` comparing :py:obj:`image1`
    with :py:obj:`image2` with :py:obj:`nslices` slices in all three axial planes

    :param name1: Name describing :py:obj:`image1`
    :type name1: str
    :param image1: Image file name to show (readable by :py:mod:`nibabel`)
    :type image1: str
    :param name2: Name describing :py:obj:`image2`
    :type name2: str
    :param image2: Image file name to show (readable by :py:mod:`nibabel`)
    :type image2: str
    :param out_file: File name
    :type out_file: path-like object
    :param nslices: Number of slices to show in each plane
    :type nslices: int
    :param form: Include a QC form in the output
    :type form: bool
    """
    svg1str = _imshow(image1, nslices)
    svg2str = _imshow(image2, nslices)

    svg1str = _set_svg_class(svg1str, 'first')
    svg2str = _set_svg_class(svg2str, 'second')
    _render(out_file, 'compare.tpl', {'name1': name1, 'name2': name2,
                                      'svg1': svg1str, 'svg2': svg2str,
                                      'form': form,
                                      'name_no_spaces': '_'.join([nametmp.replace(' ', '_') for nametmp in [name1, name2]])})


def contours(name, image, label, out_file, nslices=7, form=True):
    """Write an html file to :py:obj:`out_file` showing the :py:obj:`image`
    with :py:obj:`nslices` slices in all three axial planes. Include contour
    lines outlining the areas defined by :py:obj:`labels`.

    :param name: Name describing :py:obj:`image`
    :type name: str
    :param image: Image file name to show (readable by :py:mod:`nibabel`)
    :type image: str
    :param label: Label file name to draw contours from (readable by :py:mod:`nibabel`)
    :type label: str
    :param out_file: File name
    :type out_file: path-like object
    :param nslices: Number of slices to show in each plane
    :type nslices: int
    :param form: Include a QC form in the output
    :type form: bool
    """
    _single_opt_contours(name, image, out_file, nslices=nslices, label=label, form=form)


def _read_dists(distfile):
    dists = defaultdict(list)
    with open(distfile, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            dists[int(row[1].strip(' .'))].append(float(row[0]))
    return dists


def distributions(name, distfile, out_file, labelmap=None, form=True):
    """Write an html file to :py:obj:`out_file` showing the distributions
    defined in :py:obj:`distfile`.

    :param name: Name describing :py:obj:`distfile`
    :type name: str
    :param image: Distribution file name.
                  Must be a comma-separated file with two columns and no heading.
                  The first column is a point in distribution, and the second
                  is an integer indicating which distribution it belongs to.
    :type image: path-like object
    :param out_file: File name
    :type out_file: path-like object
    :param labelmap: Mapping of distribution labels to string labels.
    :type labelmap: dict
    :param form: Include a QC form in the output
    :type form: bool
    """
    dists = _read_dists(distfile)
    svg = plotdists(dists, labelmap=labelmap)
    _render(out_file, 'plot.tpl', {'name': name, 'svg': svg, 'form': form, 'name_no_spaces': name.replace(' ', '_')})


def plotdists(dists, labelmap=None, bins=20, alpha=0.5):
    svg = StringIO()
    fig = figure.Figure(figsize=PLOTSIZE)
    ax = fig.add_subplot(1, 1, 1)
    if labelmap is None:
        labelmap = {key: key for key in dists.keys()}
    for key, dist in dists.items():
        ax.hist(dist, bins=bins, alpha=alpha, label=labelmap[key])
    ax.legend()
    FigureCanvasSVG(fig).print_svg(svg)
    svg.seek(0)
    return svg.read()


def assemble(out_file, in_files, title, form=True):
    """combine multiple html files into one file

    :param out_file: output html file
    :type out_file: path-like object
    :param in_files: list of input files to include
    :type in_files: list of path-like objects
    :param title: title of html page
    :type title: str
    :param form: inputs contain QC forms
    :type form: bool
    """
    env = jinja2.Environment(loader=jinja2.PackageLoader('pndniworkflows', 'templates'))
    template = env.get_template('base.tpl')
    body = '\n'.join((_load(in_f) for in_f in in_files))
    out = template.render({'body': body, 'title': title, 'form': form})
    _dump(out_file, out)


def index(out_file, in_files):
    """
    Construct an html file linking all to other files

    :param out_file: output html file with links
    :type out_file: path-like object
    :param in_file: list of html files to link to from out_file
    :type in_file: list of path-like object
    """
    env = jinja2.Environment(loader=jinja2.PackageLoader('pndniworkflows', 'templates'))
    template = env.get_template('index.tpl')
    out = template.render({'urls': in_files})
    _dump(out_file, out)
