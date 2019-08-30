from pndniworkflows import postprocessing
from collections import OrderedDict
import pytest
import os
import csv
import numpy as np
import nibabel
from pathlib import Path


@pytest.fixture()
def cdtmppath(tmp_path):
    curdir = os.getcwd()
    os.chdir(str(tmp_path))
    yield tmp_path
    os.chdir(curdir)


@pytest.fixture()
def niifiles(cdtmppath):
    x = np.array([1, 2, 3, 4, 5])
    im = np.array([1, 1, 0, 3, 0])
    affine = np.array([[2.0, 0.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0, 0.0],
                       [0.0, 0.0, 1.0, 0.0],
                       [0.0, 0.0, 0.0, 1.0]])
    nibabel.Nifti1Image(x, affine).to_filename('x.nii')
    nibabel.Nifti1Image(im, affine).to_filename('im.nii')
    labels = [OrderedDict(index=1, name='T1'),
              OrderedDict(index=3, name='T3')]
    return str(Path('x.nii').resolve()), str(Path('im.nii').resolve()), labels, cdtmppath


@pytest.mark.skipif(os.getenv('FSLDIR') is None, reason='FSL not loaded')
def test_image_stats_wf(niifiles):
    wf = postprocessing.image_stats_wf(['volume', 'mean'], niifiles[2], 'testwf')
    wf.inputs.inputspec.in_file = niifiles[0]
    wf.inputs.inputspec.index_mask_file = niifiles[1]
    wd = niifiles[3] / 'wd'
    wd.mkdir()
    wf.base_dir = str(wd)
    wf.run()
    out = wd / 'testwf' / 'write' / 'out.tsv'
    with open(out, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header, data1, data3 = list(reader)
        assert header == ['index', 'name', 'number_voxels', 'volume', 'mean']
        assert data1 == ['1', 'T1', '2.0', '4.0', '1.5']
        assert data3 == ['3', 'T3', '1.0', '2.0', '4.0']
