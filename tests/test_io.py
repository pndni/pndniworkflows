from pndniworkflows.interfaces.io import WriteFSLStats, WriteBIDSFile, WriteFile, RenameAndCheckExtension, MismatchedExtensionError, ExportFile
import pytest
import csv
from pathlib import Path
from collections import OrderedDict
from utils import cdtmppath


def test_write_bids(cdtmppath):
    testnii = Path('test.nii')
    testnii.write_text('testnii')
    testh5 = Path('test.h5')
    testh5.write_text('testh5')
    testtsv = Path('test.tsv')
    testtsv.write_text('testtsv')
    testhtml = Path('test.html')
    testhtml.write_text('testhtml')
    outpath = (cdtmppath / 'out').resolve()
    outpath.mkdir()
    labelinfo = [OrderedDict(index=1, name='T1')]
    testlist = [({'suffix': 'T1w', 'subject': '1'}, testnii, 'sub-1/anat/sub-1_T1w.nii', None),
                ({'suffix': 'T2w', 'subject': '2', 'reconstruction': 'somalg'}, testnii, 'sub-2/anat/sub-2_rec-somalg_T2w.nii', None),
                ({'subject': 'abc', 'skullstripped': 'true', 'desc': 'nucor', 'suffix': 'T1w'}, testnii,
                 'sub-abc/anat/sub-abc_skullstripped-true_desc-nucor_T1w.nii', None),
                ({'subject': '1', 'desc': 'brain', 'suffix': 'mask', 'space': 'T1w'}, testnii,
                 'sub-1/anat/sub-1_space-T1w_desc-brain_mask.nii', None),
                ({'subject': '1', 'from': 'MNI152', 'to': 'T1w', 'suffix': 'xfm', 'mode': 'image'}, testh5,
                 'sub-1/xfm/sub-1_from-MNI152_to-T1w_mode-image_xfm.h5', None),
                ({'subject': '1', 'space': 'T1w', 'suffix': 'T1w', 'desc': 'MNI152'}, testnii,
                 'sub-1/anat/sub-1_space-T1w_desc-MNI152_T1w.nii', None),
                ({'subject': '1', 'space': 'T1w', 'suffix': 'mask', 'desc': 'MNI152brain'}, testnii,
                 'sub-1/anat/sub-1_space-T1w_desc-MNI152brain_mask.nii', None),
                ({'subject': '1', 'suffix': 'dseg', 'space': 'T1w', 'desc': 'tissue'}, testnii,
                 'sub-1/anat/sub-1_space-T1w_desc-tissue_dseg.nii', labelinfo),
                ({'subject': '1', 'suffix': 'stats', 'desc': 'tissue+lobes'}, testtsv,
                 'sub-1/anat/sub-1_desc-tissue+lobes_stats.tsv', None),
                ({'subject': '1'}, testhtml,
                 'sub-1/sub-1.html', None)]
    for params, in_, truth, labels in testlist:
        w = WriteBIDSFile()
        w.inputs.out_dir = str(outpath)
        w.inputs.bidsparams = params
        w.inputs.in_file = str(in_.resolve())
        if labels:
            w.inputs.labelinfo = labels
        r = w.run()
        assert r.outputs.out_file == str(outpath / truth)
        assert Path(r.outputs.out_file).read_text() == (outpath / truth).read_text()
        if labels:
            assert r.outputs.out_labelfile == str(outpath / truth).replace('.nii', '_labels.tsv')
            assert Path(r.outputs.out_labelfile).read_text() == 'index\tname\n1\tT1\n'


def test_write_tsv(cdtmppath):
    stats = ['s1', 's2', 's3']
    labels = {1: 'l1', 3: 'l3'}
    data = [1., 2., 3., 0., 0., 0., 7., 8., 9.]
    w = WriteFSLStats()
    w.inputs.statnames = stats
    w.inputs.labels = labels
    w.inputs.data = data
    w.run()
    with open('out.tsv', 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header, data1, data3 = list(reader)
    assert header == ['index', 'name', 's1', 's2', 's3']
    assert data1 == ['1', 'l1', '1.0', '2.0', '3.0']
    assert data3 == ['3', 'l3', '7.0', '8.0', '9.0']
    with pytest.raises(RuntimeError):
        # file already exists
        w.run()


def test_write_tsv_fail(cdtmppath):
    stats = ['s1', 's2', 's3']
    labels = {1: 'l1', 3: 'l3'}
    data = [1, 2, 3, 1, 0, 0, 7, 8, 9]
    w = WriteFSLStats()
    w.inputs.statnames = stats
    w.inputs.labels = labels
    w.inputs.data = data
    with pytest.raises(ValueError):
        w.run()


def test_write_tsv_docstr(cdtmppath):
    stats = ['mean', 'std']
    labels = {1: 'GM', 2: 'WM'}
    data = [1, 2, 3, 4]
    w = WriteFSLStats()
    w.inputs.statnames = stats
    w.inputs.labels = labels
    w.inputs.data = data
    w.run()
    assert Path('out.tsv').read_text() == 'index\tname\tmean\tstd\n1\tGM\t1\t2\n2\tWM\t3\t4\n'


def test_write_tsv_docstr2(cdtmppath):
    stats = ['mean', 'std']
    labels = {1: 'GM', 3: 'CSF'}
    data = [1, 2, 0, 0, 3, 4]
    w = WriteFSLStats()
    w.inputs.statnames = stats
    w.inputs.labels = labels
    w.inputs.data = data
    w.run()
    assert Path('out.tsv').read_text() == 'index\tname\tmean\tstd\n1\tGM\t1\t2\n3\tCSF\t3\t4\n'


def test_write_tsv_docstr3(cdtmppath):
    stats = ['mean', 'std']
    labels = {1: 'GM', 3: 'CSF'}
    data = [1, 2, 3, 4]
    w = WriteFSLStats()
    w.inputs.statnames = stats
    w.inputs.labels = labels
    w.inputs.data = data
    with pytest.raises(ValueError):
        w.run()


def test_write_file(cdtmppath):
    w = WriteFile()
    w.inputs.string = 'hi\r\nthere\r\n'
    r = w.run()
    with open(r.outputs.out_file, 'r', newline='') as f:
        assert f.read() == 'hi\r\nthere\r\n'
    w = WriteFile()
    w.inputs.string = 'hi\r\nthere\r\n'
    w.inputs.newline = ''
    r = w.run()
    with open(r.outputs.out_file, 'r', newline='') as f:
        assert f.read() == 'hi\r\nthere\r\n'
    w = WriteFile()
    w.inputs.string = 'hi\nthere\n'
    w.inputs.newline = '\r\n'
    r = w.run()
    with open(r.outputs.out_file, 'r', newline='') as f:
        assert f.read() == 'hi\r\nthere\r\n'


def test_RenameAndCheckExtension(tmp_path):
    testin = tmp_path / 'in.txt'
    testin.write_text('hi')
    i = RenameAndCheckExtension()
    i.inputs.in_file = testin
    i.inputs.format_string = str(Path(tmp_path / 'out.tsv'))
    with pytest.raises(MismatchedExtensionError):
        i.run()
    i.inputs.format_string = str(Path(tmp_path / 'out.txt'))
    i.run()


def test_ExportFile(tmp_path):
    testin = tmp_path / 'in.txt'
    testin.write_text('test string')
    i = ExportFile()
    i.inputs.in_file = testin
    i.inputs.out_file = tmp_path / 'out.tsv'
    i.inputs.check_extension = True
    with pytest.raises(MismatchedExtensionError):
        i.run()
    i.inputs.check_extension = False
    i.run()
    assert (tmp_path / 'out.tsv').read_text() == 'test string'
    i.inputs.out_file = tmp_path / 'out.txt'
    i.inputs.check_extension = True
    i.run()
    assert (tmp_path / 'out.txt').read_text() == 'test string'
    with pytest.raises(FileExistsError):
        i.run()
    i.inputs.clobber = True
    i.run()
    assert (tmp_path / 'out.txt').read_text() == 'test string'
