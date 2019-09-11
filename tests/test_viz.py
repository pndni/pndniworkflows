from pndniworkflows import viz
import nibabel
import numpy as np
import pytest
from nipype import utils as nputils
from nipype.pipeline import engine as pe
from nipype.interfaces import IdentityInterface


def test_read_dists(tmp_path):
    distfile = tmp_path / 'dists.txt'
    distfile.write_text('1.5,1\n2.0,1\n1.5,2')
    dist = viz._read_dists(distfile)
    assert dist == {1: [1.5, 2.0], 2: [1.5]}


def test_distributions(tmp_path):
    distfile = tmp_path / 'dists.txt'
    distfile.write_text('1.5,1\n2.0,1')
    outfile = tmp_path / 'out.txt'
    labelfile = tmp_path / 'labels.tsv'
    labelfile.write_text('index\tname\n1\tGM\n')
    viz.distributions('testdist', distfile, outfile, labelfile)


def test_distributions_dne(tmp_path):
    outfile = tmp_path / 'out.txt'
    labelfile = tmp_path / 'labels.tsv'
    labelfile.write_text('index\tname\n1\tGM\n')
    viz.distributions('testdist', None, outfile, labelfile)


@pytest.fixture()
def images(tmp_path):
    image1 = str(tmp_path / 'image1.nii')
    image2 = str(tmp_path / 'image2.nii')
    nibabel.Nifti1Image(np.array([[[1, 2, 3, 4]]]).reshape(1, 2, 2), np.eye(4)).to_filename(image1)
    nibabel.Nifti1Image(np.arange(8).reshape(2, 2, 2), np.eye(4)).to_filename(image2)
    image3 = None
    return tmp_path, image1, image2, image3


def test_single(images):
    tmp_path, image1, image2, image3 = images
    outfile = tmp_path / 'out.txt'
    viz.single('testsingle', image1, outfile, nslices=1)
    viz.single('testsingle', image3, outfile, nslices=1)


def test_contour(images):
    tmp_path, image1, image2, image3 = images
    outfile = tmp_path / 'out.txt'
    viz.contours('testcontours', image1, image2, outfile, nslices=1)
    viz.contours('testcontours', image3, image2, outfile, nslices=1)
    viz.contours('testcontours', image2, image3, outfile, nslices=1)


def test_compare(images):
    tmp_path, image1, image2, image3 = images
    outfile = tmp_path / 'out.txt'
    viz.compare('testcompare', image1, 'testcompare2', image2, outfile, nslices=1)
    viz.compare('testcompare', image3, 'testcompare2', image2, outfile, nslices=1)
    viz.compare('testcompare', image2, 'testcompare2', image3, outfile, nslices=1)


def test_crash(tmp_path):
    fakenode = pe.Node(IdentityInterface(['field1']), 'name')
    traceback = ['test\n', 'string\n']
    pklfile = tmp_path / 'test.pklz'
    outfile = tmp_path / 'out.txt'
    nputils.filemanip.savepkl(str(pklfile), {'node': fakenode, 'traceback': traceback}, versioning=True)
    viz.crash('testcrash', [str(pklfile)], str(outfile))
    outstr = outfile.read_text()
    assert 'class="crash"' in outstr
    assert 'class="success"' not in outstr
    viz.crash('testcrash', [], str(outfile))
    outstr = outfile.read_text()
    assert 'class="crash"' not in outstr
    assert 'class="success"' in outstr
