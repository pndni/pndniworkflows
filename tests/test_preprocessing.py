import nibabel
import numpy as np
from utils import cdtmppath
from pndniworkflows.utils import Points, SinglePoint, cutimage
from pndniworkflows.preprocessing import crop_wf, neck_removal_wf
from pndniworkflows.interfaces.io import ExportFile
import pytest
import os
from nipype.pipeline import engine as pe


CUTEXPS = [([[1, 5, 6], [5, 2, 9], [8, 3, 3]], (slice(1, 9), slice(2, 6), slice(3, 10))),
           ([[-1, 5, 6], [5, 2, 9], [8, 3, 100]], (slice(0, 9), slice(2, 6), slice(6, 12))),
           ([[1.1, 4.9, 6], [5, 2, 9], [7.8, 3, 3.2]], (slice(1, 9), slice(2, 6), slice(3, 10)))]


NECKEXPS = [([[1, 5, 6], [5, 2, 9], [8, 3, 3]], [0, 0, 3], slice(3, None)),
            ([[-1, 5, 6], [5, -2, -2], [8, 3, 100]], [0, 0, -2], slice(0, None)),
            ([[1.1, 4.9, 6], [5, 2, 9], [7.8, 3, 3.2]], [7.8, 3, 3.2], slice(3, None))]


@pytest.mark.parametrize('inpoints,truth', CUTEXPS)
def test_cutimage(cdtmppath, inpoints, truth):
    arr = np.arange(10 * 11 * 12).reshape((10, 11, 12))
    aff = np.eye(4)
    ni = nibabel.Nifti1Image(arr, aff)
    ni.to_filename('in.nii')
    points = Points([SinglePoint(pt[0], pt[1], pt[2], 0) for pt in inpoints])
    points.to_tsv('points.tsv')
    cutimage('in.nii', 'points.tsv', False)
    niout = nibabel.load('in_cropped.nii')
    assert np.all(niout.get_fdata() == arr[truth])
    for model in [True, False]:
        wfwrapper = pe.Workflow('wrapper')
        wf = crop_wf()
        wf.inputs.inputspec.T1 = os.path.abspath('in.nii')
        wf.inputs.inputspec.points = os.path.abspath('points.tsv')
        if model:
            wf.inputs.inputspec.model = os.path.abspath('in.nii')
        export = pe.Node(ExportFile(out_file=os.path.abspath('out2.nii'), clobber=True), 'exp')
        wfwrapper.connect(wf, 'outputspec.cropped', export, 'in_file')
        wfwrapper.run()
        niout2 = nibabel.load('out2.nii')
        assert np.all(niout2.get_fdata() == arr[truth])


@pytest.mark.parametrize('inpoints,limits,truth', NECKEXPS)
def test_cropneck(cdtmppath, inpoints, limits, truth):
    arr = np.arange(10 * 11 * 12).reshape((10, 11, 12))
    aff = np.eye(4)
    ni = nibabel.Nifti1Image(arr, aff)
    ni.to_filename('in.nii')
    points = Points([SinglePoint(pt[0], pt[1], pt[2], 0) for pt in inpoints])
    points.to_tsv('points.tsv')
    cutimage('in.nii', 'points.tsv', True)
    niout = nibabel.load('in_cropped.nii')
    assert np.all(niout.get_fdata() == arr[:, :, truth])
    for model in [True, False]:
        wfwrapper = pe.Workflow('wrapper')
        wf = neck_removal_wf()
        wf.inputs.inputspec.T1 = os.path.abspath('in.nii')
        wf.inputs.inputspec.limits = limits
        if model:
            wf.inputs.inputspec.model = os.path.abspath('in.nii')
        export = pe.Node(ExportFile(out_file=os.path.abspath('out2.nii'), clobber=True), 'exp')
        wfwrapper.connect(wf, 'outputspec.cropped', export, 'in_file')
        wfwrapper.run()
        niout2 = nibabel.load('out2.nii')
        assert np.all(niout2.get_fdata() == arr[:, :, truth])
