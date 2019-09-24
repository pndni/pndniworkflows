from pndniworkflows import utils
from pndniworkflows.interfaces.utils import ConvertPoints, Gzip
from collections import OrderedDict
import pytest
from io import StringIO
import csv
import os
import tempfile
import gzip
from pathlib import Path


def test_combine_labels():
    in1 = [OrderedDict(index=1, name='T1'),
           OrderedDict(index=2, name='T2')]
    in2 = [OrderedDict(index=1, name='T3'),
           OrderedDict(index=2, name='T4')]
    out = utils.combine_labels(in1, in2)
    indices = [1, 2, 3, 4]
    names = ['T1+T3', 'T2+T3', 'T1+T4', 'T2+T4']
    for outtmp, index, name in zip(out, indices, names):
        assert outtmp['index'] == index
        assert outtmp['name'] == name


def test_combine_labels2():
    in1 = [OrderedDict(index=1, name='T1'),
           OrderedDict(index=2, name='T2'),
           OrderedDict(index=3, name='T3')]
    in2 = [OrderedDict(index=1, name='T4'),
           OrderedDict(index=2, name='T5')]
    out = utils.combine_labels(in1, in2)
    indices = list(range(1, 7))
    names = ['T1+T4', 'T2+T4', 'T3+T4', 'T1+T5', 'T2+T5', 'T3+T5']
    for outtmp, index, name in zip(out, indices, names):
        assert outtmp['index'] == index
        assert outtmp['name'] == name


def test_combine_labels3():
    in1 = [OrderedDict(index=1, name='A1'),
           OrderedDict(index=2, name='A2'),
           OrderedDict(index=3, name='A3')]
    in2 = [OrderedDict(index=1, name='B1'),
           OrderedDict(index=2, name='B2')]
    in3 = [OrderedDict(index=4, name='C4'),
           OrderedDict(index=5, name='C5')]
    out = utils.combine_labels(in1, in2, in3)
    indices = [19, 20, 21, 22, 23, 24,
               25, 26, 27, 28, 29, 30]
    names = ['A1+B1+C4', 'A2+B1+C4', 'A3+B1+C4',
             'A1+B2+C4', 'A2+B2+C4', 'A3+B2+C4',
             'A1+B1+C5', 'A2+B1+C5', 'A3+B1+C5',
             'A1+B2+C5', 'A2+B2+C5', 'A3+B2+C5']
    for outtmp, index, name in zip(out, indices, names):
        assert outtmp['index'] == index
        assert outtmp['name'] == name


def test_combine_labels4():
    in1 = [OrderedDict(index=1, name='T1', abbr='blah'),
           OrderedDict(index=2, name='T2', abbr='blah2')]
    in2 = [OrderedDict(index=1, name='T3'),
           OrderedDict(index=2, name='T4')]
    out = utils.combine_labels(in1, in2)
    indices = [1, 2, 3, 4]
    names = ['T1+T3', 'T2+T3', 'T1+T4', 'T2+T4']
    abbrs = ['blah+', 'blah2+', 'blah+', 'blah2+']
    for outtmp, index, name, abbrs in zip(out, indices, names, abbrs):
        assert outtmp['index'] == index
        assert outtmp['name'] == name


def test_combine_labels5():
    in1 = [OrderedDict(index=1, name='T1', abbr='blah'),
           OrderedDict(index=2, name='T2')]
    in2 = [OrderedDict(index=1, name='T3'),
           OrderedDict(index=2, name='T4')]
    with pytest.raises(ValueError):
        utils.combine_labels(in1, in2)


def test_combine_labels6():
    in1 = [OrderedDict(index=1, name='T1'),
           OrderedDict(index=2, name='T2')]
    in2 = [OrderedDict(index=1),
           OrderedDict(index=2)]
    with pytest.raises(ValueError):
        utils.combine_labels(in1, in2)


def test_combine_labels7():
    in1 = [OrderedDict(name='T1'),
           OrderedDict(name='T2')]
    in2 = [OrderedDict(index=1, name='T3'),
           OrderedDict(index=2, name='T4')]
    with pytest.raises(ValueError):
        utils.combine_labels(in1, in2)


def test_combine_labels8():
    in1 = [OrderedDict(index=8, name='T1'),
           OrderedDict(index=8, name='T2')]
    in2 = [OrderedDict(index=1, name='T3'),
           OrderedDict(index=2, name='T4')]
    with pytest.raises(ValueError):
        utils.combine_labels(in1, in2)


def test_combine_labels9():
    in1 = [OrderedDict(index=8, name='T1'),
           OrderedDict(index=9, name='T1')]
    in2 = [OrderedDict(index=1, name='T3'),
           OrderedDict(index=2, name='T4')]
    with pytest.raises(ValueError):
        utils.combine_labels(in1, in2)


def test_ensure_uniq_1():
    x = [1, 2, 3, 4]
    assert utils.unique(x)
    x[3] = 2
    assert not utils.unique(x)


def test_ensure_uniq_2():
    x = [{1: 'a'}, {2: 'b'}, {3: 'c'}, {4: 'd'}]
    assert utils.unique(x)
    x[3] = {2: 'b'}
    assert not utils.unique(x)


def test_ensure_uniq_3():
    x = [{1: 'a'}, {1: 'b'}, {1: 'c'}, {1: 'd'}]
    assert utils.unique(x)


def test_first_nonique():
    x = [1, 2, 3, 2]
    assert utils.first_nonunique(x) == 2


def test_first_nonique():
    x = [1, 4, 3, 2]
    assert utils.first_nonunique(x) is None


def test_labels2dict():
    in1 = [OrderedDict(index=1, name='T1'),
           OrderedDict(index=2, name='T2')]
    out = utils.labels2dict(in1, 'name')
    assert out[1] == 'T1'
    assert out[2] == 'T2'
    in1.append(OrderedDict(index=1, name='T3'))
    with pytest.raises(RuntimeError):
        utils.labels2dict(in1, 'name')


def test_chunk():
    x = [1, 2, 3, 4, 5, 6]
    y = list(utils.chunk(x, 3))
    assert y[0] == x[:3]
    assert y[1] == x[3:]
    assert len(y) == 2
    y = list(utils.chunk(x, 2))
    assert y[0] == x[:2]
    assert y[1] == x[2:4]
    assert y[2] == x[4:]
    assert len(y) == 3
    y = list(utils.chunk(x, 1))
    for i in range(6):
        assert y[i] == x[i:i+1]
    assert len(y) == 6
    with pytest.raises(RuntimeError):
        y = list(utils.chunk(x, 4))


def test_tsv_to_flat_dict(tmp_path):
    tmp_file = tmp_path / 'test.tsv'
    tmp_file.write_text('\tc1\tc2\tc3\n'
                        'r1\t1\t2\t3\n'
                        'r2\t4\t5\t6\n')
    out = utils.tsv_to_flat_dict(tmp_file)
    assert set(out.keys()) == {'r1_c1', 'r1_c2', 'r1_c3',
                               'r2_c1', 'r2_c2', 'r2_c3'}
    assert out['r1_c1'] == '1'
    assert out['r1_c2'] == '2'
    assert out['r1_c3'] == '3'
    assert out['r2_c1'] == '4'
    assert out['r2_c2'] == '5'
    assert out['r2_c3'] == '6'
    out = utils.tsv_to_flat_dict(tmp_file, index='')
    assert set(out.keys()) == {'r1_c1', 'r1_c2', 'r1_c3',
                               'r2_c1', 'r2_c2', 'r2_c3'}
    assert out['r1_c1'] == '1'
    assert out['r1_c2'] == '2'
    assert out['r1_c3'] == '3'
    assert out['r2_c1'] == '4'
    assert out['r2_c2'] == '5'
    assert out['r2_c3'] == '6'
    out = utils.tsv_to_flat_dict(tmp_file, ignore=['c2'])
    assert set(out.keys()) == {'r1_c1', 'r1_c3',
                               'r2_c1', 'r2_c3'}
    assert out['r1_c1'] == '1'
    assert out['r1_c3'] == '3'
    assert out['r2_c1'] == '4'
    assert out['r2_c3'] == '6'
    out = utils.tsv_to_flat_dict(tmp_file, index='c3')
    assert set(out.keys()) == {'3_c1', '3_c2', '3_',
                               '6_c1', '6_c2', '6_'}
    assert out['3_c1'] == '1'
    assert out['3_c2'] == '2'
    assert out['3_'] == 'r1'
    assert out['6_c1'] == '4'
    assert out['6_c2'] == '5'
    assert out['6_'] == 'r2'
    out = utils.tsv_to_flat_dict(tmp_file, index='c3', ignore=['c1'])
    assert set(out.keys()) == {'3_c2', '3_',
                               '6_c2', '6_'}
    assert out['3_c2'] == '2'
    assert out['3_'] == 'r1'
    assert out['6_c2'] == '5'
    assert out['6_'] == 'r2'
    tmp_file.write_text('\tc1\tc2\tc3\n'
                        'r1\t1\t2\t3\n'
                        'r1\t4\t5\t6\n')
    with pytest.raises(ValueError):
        out = utils.tsv_to_flat_dict(tmp_file, index='c3', ignore=['c3'])
    with pytest.raises(RuntimeError):
        utils.tsv_to_flat_dict(tmp_file)
    tmp_file.write_text('\tc1\tc2\tc1\n'
                        'r1\t1\t2\t3\n'
                        'r2\t4\t5\t6\n')
    with pytest.raises(RuntimeError):
        utils.tsv_to_flat_dict(tmp_file)


def test_combine_stats_files(tmp_path):
    sub1 = tmp_path / 'sub-1' / 'anat' / 'sub-1_stats.tsv'
    sub1.parent.mkdir(parents=True)
    sub1.write_text('\tc1\tc2\tc3\n'
                    'r1\ts1_1\ts1_2\ts1_3\n'
                    'r2\ts1_4\ts1_5\ts1_6\n')
    sub2 = tmp_path / 'sub-2' / 'anat' / 'sub-2_stats.tsv'
    sub2.parent.mkdir(parents=True)
    sub2.write_text('\tc1\tc2\tc3\n'
                    'r1\ts2_1\ts2_2\ts2_3\n'
                    'r2\ts2_4\ts2_5\ts2_6\n')
    sub2a1 = tmp_path / 'sub-2' / 'anat' / 'sub-2_acq-1_stats.tsv'
    sub2a1.write_text('\tc1\tc2\tc3\n'
                      'r1\ts2a1_1\ts2a1_2\ts2a1_3\n'
                      'r2\ts2a1_4\ts2a1_5\ts2a1_6\n')
    outf = StringIO()
    utils.combine_stats_files(str(tmp_path), False,
                              ['subject', 'acquisition'],
                              {'datatype': 'anat', 'extension': 'tsv'},
                              outf)
    outf.seek(0)
    reader = csv.DictReader(outf, delimiter='\t')
    outf2 = StringIO()
    utils.combine_stats_files(str(tmp_path), False,
                              ['subject', 'acquisition'],
                              {},
                              outf2, strict=False)
    outf2.seek(0)
    reader2 = csv.DictReader(outf2, delimiter='\t')
    outtruth = {'1': {None: {'r1_c1': 's1_1',
                             'r1_c2': 's1_2',
                             'r1_c3': 's1_3',
                             'r2_c1': 's1_4',
                             'r2_c2': 's1_5',
                             'r2_c3': 's1_6'}
                      },
                '2': {None: {'r1_c1': 's2_1',
                             'r1_c2': 's2_2',
                             'r1_c3': 's2_3',
                             'r2_c1': 's2_4',
                             'r2_c2': 's2_5',
                             'r2_c3': 's2_6'},
                      '1': {'r1_c1': 's2a1_1',
                            'r1_c2': 's2a1_2',
                            'r1_c3': 's2a1_3',
                            'r2_c1': 's2a1_4',
                            'r2_c2': 's2a1_5',
                            'r2_c3': 's2a1_6'}}
                }
    for readertmp in [reader, reader2]:
        for row in readertmp:
            assert set(row.keys()) == {'subject', 'acquisition', 'r1_c1', 'r1_c2', 'r1_c3', 'r2_c1', 'r2_c2', 'r2_c3'}
            for k in ['r1_c1', 'r1_c2', 'r1_c3', 'r2_c1', 'r2_c2', 'r2_c3']:
                if len(row['acquisition']) == 0:
                    acqkey = None
                else:
                    acqkey = row['acquisition']
                assert row[k] == outtruth[row['subject']][acqkey][k]

    outf = StringIO()
    with pytest.raises(utils.UnaccountedBidsPropertiesError):
        utils.combine_stats_files(str(tmp_path), False,
                                  ['subject'],
                                  {'datatype': 'anat', 'extension': 'tsv'},
                                  outf)
    outf = StringIO()
    with pytest.raises(utils.ColumnExistsError):
        utils.combine_stats_files(str(tmp_path), False,
                                  ['subject'],
                                  {'datatype': 'anat', 'extension': 'tsv'},
                                  outf, strict=False)
    outf = StringIO()
    with pytest.raises(utils.InvariantViolationError):
        utils.combine_stats_files(str(tmp_path), False,
                                  ['subject', 'acquisition'],
                                  {'datatype': 'func', 'extension': 'tsv'},
                                  outf)
    outf = StringIO()
    with pytest.raises(utils.ColumnExistsError):
        utils.combine_stats_files(str(tmp_path), False,
                                  ['subject', 'acquisition', 'r1_c1'],
                                  {'datatype': 'anat', 'extension': 'tsv'},
                                  outf)
    sub3r1 = tmp_path / 'sub-3' / 'anat' / 'sub-3_rec-1_stats.tsv'
    sub3r1.parent.mkdir(parents=True)
    sub3r1.write_text('\tc1\tc2\tc3\n'
                      'r1\ts3r1_1\ts3r1_2\ts3r1_3\n'
                      'r2\ts3r1_4\ts3r1_5\ts3r1_6\n')
    outf = StringIO()
    with pytest.raises(utils.UnaccountedBidsPropertiesError):
        utils.combine_stats_files(str(tmp_path), False,
                                  ['subject', 'acquisition'],
                                  {'datatype': 'anat', 'extension': 'tsv'},
                                  outf)
    outf = StringIO()
    utils.combine_stats_files(str(tmp_path), False,
                              ['subject', 'acquisition'],
                              {'datatype': 'anat', 'extension': 'tsv'},
                              outf, strict=False)
    outtruth['3'] = {None: {'r1_c1': 's3r1_1',
                            'r1_c2': 's3r1_2',
                            'r1_c3': 's3r1_3',
                            'r2_c1': 's3r1_4',
                            'r2_c2': 's3r1_5',
                            'r2_c3': 's3r1_6'}}
    for row in reader:
        assert set(row.keys()) == {'subject', 'acquisition', 'r1_c1', 'r1_c2', 'r1_c3', 'r2_c1', 'r2_c2', 'r2_c3'}
        for k in ['r1_c1', 'r1_c2', 'r1_c3', 'r2_c1', 'r2_c2', 'r2_c3']:
            if len(row['acquisition']) == 0:
                acqkey = None
            else:
                acqkey = row['acquisition']
            assert row[k] == outtruth[row['subject']][acqkey][k]


def test_combine_stats_files_docstring(tmp_path):
    sub1 = tmp_path / 'sub-1' / 'anat' / 'sub-1_stats.tsv'
    sub1.parent.mkdir(parents=True)
    sub1.write_text('index\tname\tvolume\tmean\n'
                    '1\tGM\t10\t20.0\n'
                    '2\tWM\t5\t30.0\n')
    sub2 = tmp_path / 'sub-2' / 'anat' / 'sub-2_stats.tsv'
    sub2.parent.mkdir(parents=True)
    sub2.write_text('index\tname\tvolume\tmean\n'
                    '1\tGM\t11\t19.0\n'
                    '2\tWM\t6\t31.0\n')
    sub2a1 = tmp_path / 'sub-2' / 'anat' / 'sub-2_acq-1_stats.tsv'
    sub2a1.write_text('index\tname\tvolume\tmean\n'
                      '1\tGM\t8\t25.0\n'
                      '2\tWM\t4\t40.0\n')
    outfile = tmp_path / 'outfile.tsv'
    with open(str(outfile), 'w') as f:
        utils.combine_stats_files(str(tmp_path), False, ('subject', 'acquisition'),
                                  {'datatype': 'anat', 'extension': 'tsv'}, f,
                                  index='name', ignore=['index'])
    assert outfile.read_text() == ('subject\tacquisition\tGM_volume\tGM_mean\tWM_volume\tWM_mean\n'
                                   '1\t\t10\t20.0\t5\t30.0\n'
                                   '2\t\t11\t19.0\t6\t31.0\n'
                                   '2\t1\t8\t25.0\t4\t40.0\n')


def test_write_labels(tmp_path):
    labels = [{'index': 0, 'name': 'a'}, {'index': 1, 'name': 'b'}]
    utils.write_labels(tmp_path / 'out.tsv', labels)
    s = StringIO(newline='')
    utils.write_labels(s, labels)
    s.seek(0)
    st = s.read()
    with open(tmp_path / 'out.tsv', 'r', newline='') as f:
        ft = f.read()
    assert st == ft == 'index\tname\r\n0\ta\r\n1\tb\r\n'


def cmp(f1, f2):
    with open(f1, 'r', newline='') as i1, open(f2, 'r', newline='') as i2:
        return i1.read() == i2.read()


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


def test_Points_read(points_path):
    tsv = utils.Points.from_tsv(points_path / 'simple.tsv')
    ants = utils.Points.from_ants_csv(points_path / 'ants.csv')
    minc = utils.Points.from_minc_tag(points_path / 'mni.tag')
    assert tsv == ants == minc


def test_Points_write(points_path):
    p = utils.Points([utils.SinglePoint(1.1, 1.2, 1.3, 10),
                      utils.SinglePoint(2.1, 2.2, 2.3, 20)])
    p.to_ants_csv(points_path / 'out_ants.csv')
    assert cmp(points_path / 'ants.csv', points_path / 'out_ants.csv')
    p.to_minc_tag(points_path / 'out_mni.tag')
    assert cmp(points_path / 'mni.tag', points_path / 'out_mni.tag')


@pytest.fixture
def cleandir():
    os.chdir(tempfile.mkdtemp())


@pytest.mark.usefixtures('cleandir')
@pytest.mark.parametrize('in_format,points_file', [('tsv', 'simple.tsv'), ('ants', 'ants.csv'), ('minc', 'mni.tag')])
@pytest.mark.parametrize('out_format,out_file', [('tsv', 'simple.tsv'), ('ants', 'ants.csv'), ('minc', 'mni.tag')])
def test_ConvertPoints(points_path, in_format, points_file, out_format, out_file):
    i = ConvertPoints(in_format=in_format, in_file=points_path / points_file, out_format=out_format)
    r = i.run()
    cmp(r.outputs.out_file, points_path / out_file)


@pytest.mark.usefixtures('cleandir')
def test_Gzip(tmp_path):
    in_file = tmp_path / 'test.txt'
    in_file.write_text('some text here')
    i = Gzip(in_file=in_file)
    r = i.run()
    b = Path(r.outputs.out_file).read_bytes()
    bd = gzip.decompress(b).decode()
    assert bd == 'some text here'
