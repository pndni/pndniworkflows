from pndniworkflows import viz


def test_read_dists(tmp_path):
    distfile = tmp_path / 'dists.txt'
    distfile.write_text('1.5,1\n2.0,1\n1.5,2')
    dist = viz._read_dists(distfile)
    assert dist == {1: [1.5, 2.0], 2: [1.5]}


def test_distributions(tmp_path):
    distfile = tmp_path / 'dists.txt'
    distfile.write_text('1.5,1\n2.0,1')
    outfile = tmp_path / 'out.txt'
    viz.distributions('testdist', distfile, outfile)
