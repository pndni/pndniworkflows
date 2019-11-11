from pndniworkflows import postprocessing
from collections import OrderedDict
import pytest
import os
import csv
import numpy as np
import nibabel
from pathlib import Path
from utils import cdtmppath


@pytest.fixture()
def niifiles(cdtmppath):
    x = np.array([4, 16, 16, 4, 5])
    im = np.array([1, 1, 1, 3, 0])
    affine = np.array([[2.0, 0.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0, 0.0],
                       [0.0, 0.0, 1.0, 0.0],
                       [0.0, 0.0, 0.0, 1.0]])
    nibabel.Nifti1Image(x, affine).to_filename('x.nii')
    nibabel.Nifti1Image(im, affine).to_filename('im.nii')
    labels = [OrderedDict(index=1, name='T1'),
              OrderedDict(index=3, name='T3')]
    return str(Path('x.nii').resolve()), str(Path('im.nii').resolve()), labels, cdtmppath


_stats_exps = ((['volume', 'mean'], ['number_voxels', 'volume', 'mean'], ['3.0', '6.0', '12.0'], ['1.0', '2.0', '4.0']),
               (['median'], ['median'], ['16.0'], ['4.0']),
               (['volume', 'median', 'mean'], ['number_voxels', 'volume', 'mean', 'median'], ['3.0', '6.0', '12.0', '16.0'], ['1.0', '2.0', '4.0', '4.0']),
               (['median', 'volume', 'mean'], ['number_voxels', 'volume', 'mean', 'median'],  ['3.0', '6.0', '12.0', '16.0'], ['1.0', '2.0', '4.0', '4.0']),
               (['kurtosis', 'volume', 'median', 'mean'], ['number_voxels', 'volume', 'mean', 'kurtosis', 'median'],  ['3.0', '6.0', '12.0', '-1.5', '16.0'], ['1.0', '2.0', '4.0', '-3.0', '4.0']))


@pytest.mark.skipif(os.getenv('FSLDIR') is None, reason='FSL not loaded')
@pytest.mark.parametrize('stats,truth_header,truth1,truth2', _stats_exps)
def test_image_stats_wf(niifiles, stats, truth_header, truth1, truth2):
    wf = postprocessing.image_stats_wf(stats, niifiles[2], 'testwf')
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
        assert header == ['index', 'name'] + truth_header
        assert data1 == ['1', 'T1'] + truth1
        assert data3 == ['3', 'T3'] + truth2
