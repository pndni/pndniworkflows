import numpy as np
import nibabel
import pytest
from pndniworkflows.interfaces.pndni_utils import ForceQForm, ConvertPoints, Stats
from nipype.utils.filemanip import indirectory
import tempfile
import os
import csv


def cmp(f1, f2):
    with open(f1, 'r', newline='') as i1, open(f2, 'r', newline='') as i2:
        return i1.read() == i2.read()


@pytest.mark.parametrize('testtype', ['qform', 'sform', 'both', 'none'])
def test_forceqform(tmp_path, testtype):
    i1 = tmp_path / 'image1.nii'
    affine = np.array([[1.0, 0.0, 0.0, -20.0],
                       [0.0, 2.0, 0.0, -30.0],
                       [0.0, 0.0, 4.0, -40.0],
                       [0.0, 0.0, 0.0, 1.0]])
    img = np.arange(24).reshape(2, 3, 4)
    nii = nibabel.Nifti1Image(img, None)

    if testtype == 'qform':
        nii.set_qform(affine)
    elif testtype == 'sform':
        nii.set_sform(affine)
    elif testtype == 'both':
        nii.set_qform(affine)
        nii.set_sform(affine * 2)
    elif testtype == 'none':
        pass
    else:
        raise RuntimeError()
    nii.to_filename(str(i1))
    i = ForceQForm(in_file=i1)
    with indirectory(tmp_path):
        if testtype == 'none':
            with pytest.raises(RuntimeError):
                i.run()
            return
        res = i.run()
    nout = nibabel.load(str(res.outputs.out_file))
    assert np.all(nout.affine == affine)
    assert np.all(nout.get_qform() == affine)
    assert nout.get_sform(coded=True)[1] == 0


@pytest.fixture
def cleandir():
    os.chdir(tempfile.mkdtemp())


@pytest.fixture
def points_path(tmp_path):
    (tmp_path / 'mni.tag').write_text("""MNI Tag Point File
Volumes = 1;
Points =
 1.1 1.2 1.3 0 -1 -1 "10"
 2.1 2.2 2.3 0 -1 -1 "20";
""")
    with open(tmp_path / 'ants.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['x', 'y', 'z', 'index', 't'])
        writer.writerow([-1.1, -1.2, 1.3, 10, 0.0])
        writer.writerow([-2.1, -2.2, 2.3, 20, 0.0])

    with open(tmp_path / 'simple.tsv', 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['x', 'y', 'z', 'index'])
        writer.writerow([1.1, 1.2, 1.3, 10, 0.0])
        writer.writerow([2.1, 2.2, 2.3, 20, 0.0])
    return tmp_path


@pytest.mark.usefixtures('cleandir')
@pytest.mark.parametrize('in_format,points_file', [('tsv', 'simple.tsv'), ('ants', 'ants.csv'), ('minc', 'mni.tag')])
@pytest.mark.parametrize('out_format,out_file', [('tsv', 'simple.tsv'), ('ants', 'ants.csv'), ('minc', 'mni.tag')])
def test_ConvertPoints(points_path, in_format, points_file, out_format, out_file):
    i = ConvertPoints(in_format=in_format, in_file=points_path / points_file, out_format=out_format)
    r = i.run()
    cmp(r.outputs.out_file, points_path / out_file)


def test_Stats(tmp_path):

    inputfile = str(tmp_path / 'in.nii')
    maskfile = str(tmp_path / 'out.nii')
    input = np.arange(3 * 4 * 5).reshape(3, 4, 5).astype(np.float)
    mask = np.zeros(input.shape, dtype=np.int)
    mask[:2, 0, -1] = 1
    mask[1, 1:3, 1:3] = 2
    mask[2, 1, 1] = 4
    assert tuple(np.unique(mask)) == (0, 1, 2, 4)
    nibabel.Nifti1Image(input, np.eye(4)).to_filename(inputfile)
    nibabel.Nifti1Image(mask, np.eye(4)).to_filename(maskfile)

    i = Stats(op_string='-m -m', in_file=inputfile, index_mask_file=maskfile)
    r = i.run()
    means = np.array([np.mean(input[mask == i]) for i in range(1, 5)])
    means[np.isnan(means)] = 0.0
    assert np.all(r.outputs.out_stat == np.repeat(means, 2))
