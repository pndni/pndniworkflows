from nipype.pipeline import engine as pe
from nipype import IdentityInterface, Function
from .registration import ants_registration_affine_node
from nipype.interfaces.ants.resampling import ApplyTransformsToPoints
from nipype.interfaces.base import isdefined
from .interfaces.utils import ConvertPoints, CutImage
from .utils import Points, SinglePoint


def writepoints(limits):
    from pathlib import Path
    x, y, z = limits
    with open('points.tsv', 'w') as f:
        f.write('x\ty\tz\tindex\n')
        f.write('{}\t{}\t{}\t0\n'.format(x, y, z))
        f.write('{}\t{}\t{}\t0\n'.format(x, -y, z))
        f.write('{}\t{}\t{}\t0\n'.format(-x, -y, z))
        f.write('{}\t{}\t{}\t0\n'.format(-x, y, z))
    return str(Path('points.tsv').resolve())


def neck_removal_wf():
    """Create a workflow to to remove the neck. This workflow requires a
    model image (e.g. an MNI standard) and points on that image. The model
    is registered to the T1 image, and the points transformed into T1 space.
    The inferior most transformed point is used to determine the cutting
    plane, which is aligned with the voxel coordinates.

    :return: A :py:mod:`nipype` workflow

    Workflow inputs/outputs

    :param inputspec.T1: The T1 image to remove the neck from
    :param inputspec.model: The reference image to register to the T1 image
    :param inputspec.limits: Points in model roughly indicating the ideal cutting plane
    :return: A :py:mod:`nipype` node

    """
    name = 'neck_removal'
    wf = pe.Workflow(name)
    inputspec = pe.Node(IdentityInterface(['T1', 'model', 'limits']), name='inputspec')
    wpoints = pe.Node(Function(input_names=['limits'], output_names=['points'], function=writepoints), name='write_points')
    cut = pe.Node(CutImage(neckonly=True), name='cut')
    outputspec = pe.Node(IdentityInterface(['cropped']), name='outputspec')
    if isdefined(inputspec.inputs.model):
        trpoints = _tr_points_wf()
        wf.connect([(inputspec, trpoints, [('T1', 'inputspec.T1'),
                                           ('model', 'inputspec.model')]),
                    (wpoints, trpoints, [('points', 'inputspec.points')]),
                    (trpoints, cut, [('outputspec.out_points', 'points_file')])])
    else:
        wf.connect([(wpoints, cut, [('points', 'points_file')])])
    wf.connect([(inputspec, wpoints, [('limits', 'limits')]),
                (inputspec, cut, [('T1', 'in_file')]),
                (cut, outputspec, [('out_file', 'cropped')])])
    return wf


def crop_wf():
    """Create a workflow to to crop the image. This workflow requires a
    model image (e.g. an MNI standard) and points on that image. The model
    is registered to the T1 image, and the points transformed into T1 space.
    The image is cut to a box containing all of the transformed points.
    All cuts are in voxel coordinates.

    :return: A :py:mod:`nipype` workflow

    Workflow inputs/outputs

    :param inputspec.T1: The T1 image to remove the neck from
    :param inputspec.model: The reference image to register to the T1 image
    :param inputspec.points: Points file (tsv file with x, y, z, and index (ignored),
                             representing the limits in model space
    :return: A :py:mod:`nipype` node

    """
    name = 'crop'
    wf = pe.Workflow(name)
    inputspec = pe.Node(IdentityInterface(['T1', 'model', 'points']), name='inputspec')
    cut = pe.Node(CutImage(neckonly=False), name='cut')
    outputspec = pe.Node(IdentityInterface(['cropped']), name='outputspec')
    if isdefined(inputspec.inputs.model):
        trpoints = _tr_points_wf()
        wf.connect([(inputspec, trpoints, [('T1', 'inputspec.T1'),
                                           ('model', 'inputspec.model'),
                                           ('points', 'inputspec.points')]),
                    (trpoints, cut, [('outputspec.out_points', 'points_file')])])
    else:
        wf.connect([(inputspec, cut, [('points', 'points_file')])])
    wf.connect([(inputspec, cut, [('T1', 'in_file')]),
                (cut, outputspec, [('out_file', 'cropped')])])
    return wf


def _tr_points_wf():
    wf = pe.Workflow('trpointswf')
    inputspec = pe.Node(IdentityInterface(['T1', 'model', 'points']), 'inputspec')
    reg = pe.Node(ants_registration_affine_node(write_composite_transform=False), name='register')
    convertpoints = pe.Node(ConvertPoints(in_format='tsv', out_format='ants'), 'convert_points')
    trpoints = pe.Node(ApplyTransformsToPoints(dimension=3), name='transform_points')
    convertpoints2 = pe.Node(ConvertPoints(in_format='ants', out_format='tsv'), 'convert_points2')
    outputspec = pe.Node(IdentityInterface(['out_points']), 'outputspec')
    wf.connect([(inputspec, reg, [('T1', 'moving_image'),
                                  ('model', 'fixed_image')]),
                (inputspec, convertpoints, [('points', 'in_file')]),
                (reg, trpoints, [('forward_transforms', 'transforms')]),
                (convertpoints, trpoints, [('out_file', 'input_file')]),
                (trpoints, convertpoints2, [('output_file', 'in_file')]),
                (convertpoints2, outputspec, [('out_file', 'out_points')])])
    return wf
