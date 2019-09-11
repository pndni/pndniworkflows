from bids import layout
from bids import config as bids_config
import json
from nipype.pipeline import engine as pe
from nipype.interfaces.utility import IdentityInterface
import os
import pkg_resources
import csv
from itertools import product
from collections import defaultdict, OrderedDict
from pkg_resources import resource_filename


def get_BIDSLayout_with_conf(dir_, **kwargs):
    """Get BIDSLayout with bids, derivatives, and pndni_bids configuration files loaded"""
    if "pndni_bids" not in bids_config.get_option("config_paths"):
        layout.add_config_paths(pndni_bids=resource_filename('pndniworkflows', 'config/pndni_bids.json'))
    l = layout.BIDSLayout(dir_, config=['bids', 'derivatives', 'pndni_bids'], **kwargs)
    return l


def get_subjects_node(bids_dir, subject_list=None):
    """
    Returns a node with an iterable field "subject" containing a list of subjects,
    which can either be passed in "subject_list" or
    acquired using :py:class:`BIDSLayout` from :py:mod:`pybids`

    :param bids_dir: bids directory to search
    :param subject_list: *optional* list of subjects (instead of searching with :py:class:`BIDSLayout`)
    :return: A :py:mod:`nipype` node
    """
    subjects = pe.Node(IdentityInterface(fields=['subject']), name='subjects')
    if subject_list is None:
        subject_list = layout.BIDSLayout(bids_dir).get_subjects()
    subjects.iterables = ('subject', subject_list)
    return subjects


def write_dataset_description(bids_dir, **kwargs):
    """
    Write a minimal dataset_description.json

    :param bids_dir: dataset_description.json will be written at the root of this directory
    :param \\*\\*kwargs: parameters to be written to dataset_description.json. Must include
                         "Name" and "BIDSVersion"
    """
    for key in ['Name', 'BIDSVersion']:
        if key not in kwargs.keys():
            raise ValueError(f'{key} is a required key')
    with open(os.path.join(bids_dir, 'dataset_description.json'), 'w') as f:
        json.dump(kwargs, f, indent=4)


def read_labels(labelfile):
    """
    Read a tsv label file. Must contain an "index" column

    :param labelfile: tsv file to read
    :return: :py:obj:`list` of :py:obj:`OrderedDict` as read with csv.DictReader
             (with the index parameter converted to :py:obj:`int`)

    """
    with open(labelfile, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        out = []
        for row in reader:
            row['index'] = int(row['index'])
            out.append(row)
    return out


def labels2dict(labels, key_to_extract):
    """
    Create a dictionary from a labels list

    :param labels: :py:obj:`list` of :py:obj:`dict` where each dict contains the keys "index" and key_to_extract
    :param key_to_extract: the key in labels to map to the output dictionary value
    :result: a dictionary indexed by the labels "index" with values given by the labels :py:obj:`key_to_extract`

    :Example:

    .. doctest::

       >>> from pndniworkflows.utils import labels2dict
       >>> labels2dict([{'index': 1, 'name': 'GM'}, {'index': 2, 'name': 'WM'}], 'name')
       {1: 'GM', 2: 'WM'}
    """
    labels_dict = {}
    for row in labels:
        if row['index'] in labels_dict.keys():
            raise RuntimeError(f'index {row["index"]} appeared more than once')
        labels_dict[row['index']] = row[key_to_extract]
    return labels_dict


def write_labels(labelfile, labels):
    """Write labels to labelfile

    :param labelfile: output file name
    :param labels: :py:obj:`list` of :py:obj:`dict`, which all have the same keys
    """
    _check_same_keys(labels)
    with open(labelfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, delimiter='\t', fieldnames=list(labels[0].keys()))
        writer.writeheader()
        for row in labels:
            writer.writerow(row)


def _combine2labels(l1, l2, l1max):
    out = l1 + (l2 - 1) * l1max
    return out


def _check_same_keys(list_of_dicts):
    keys = list_of_dicts[0].keys()
    for row in list_of_dicts[1:]:
        if row.keys() != keys:
            raise ValueError('Each element of list must have the same keys')


def combine_labels(*args):
    """Combine results from read_labels into a single label map,
    using the same logic as :py:mod:`pndni.combinelabels` in :py:mod:`pndni_utils`

    :param \\*args: any number of labels, each :py:obj:`list` of :py:obj:`dict`.
                    Each dict must contain "index" and "name" keys, where
                    the values of "index" or :py:obj:`int`, and the values are unique
                    for a given list (e.g., a labels list cannot contain multiple entries
                    with the same index).
    :result: :py:obj:`list` of :py:obj:`dict` of combined labels.

    :Example:

    .. doctest::

       >>> from pndniworkflows.utils import combine_labels
       >>> labels1 = []
       >>> labels1.append({'index': 1, 'name': 'Left Hemisphere'})
       >>> labels1.append({'index': 2, 'name': 'Right Hemisphere'})
       >>> labels2 = []
       >>> labels2.append({'index': 1, 'name': 'GM'})
       >>> labels2.append({'index': 2, 'name': 'WM'})
       >>> combine_labels(labels1, labels2)
       [{'index': 1, 'name': 'Left Hemisphere+GM'}, {'index': 2, 'name': 'Right Hemisphere+GM'}, {'index': 3, 'name': 'Left Hemisphere+WM'}, {'index': 4, 'name': 'Right Hemisphere+WM'}]
    """

    # check inputs
    for lm in args:
        _check_same_keys(lm)
        keys = lm[0].keys()
        for uniquekey in ['index', 'name']:
            if uniquekey not in keys:
                raise ValueError(f'list entries must have "{uniquekey}" key')
            vals = [row[uniquekey] for row in lm]
            if len(vals) != len(set(vals)):
                raise ValueError('indices for each label table must be unique')

    out = []
    maxes = [max((row['index'] for row in lm)) for lm in args]
    keys = {k for lm in args for k in lm[0].keys()}
    for label_comb in product(*args):
        outtmp = label_comb[0].copy()
        curmax = maxes[0]
        for label, labelmax in zip(label_comb[1:], maxes[1:]):
            outtmp['index'] += (label['index'] - 1) * curmax
            curmax *= labelmax
            for key in keys:
                if key != 'index':
                    outtmp[key] = '{}+{}'.format(outtmp.get(key, ''), label.get(key, ''))
        out.append(outtmp)
    out = list(sorted(out, key=lambda x: x['index']))
    return out


def unique(x):
    """checks that list elements are unique using only the "in" operator

    :param x: list
    :return: True if elements of list are unique, False otherwise

    """
    x = x.copy()
    while len(x):
        first = x.pop(0)
        if first in x:
            return False
    return True


def chunk(iterable, chunksize):
    """Yield lists of size ``chunksize`` with elements from iterable.

    :param iterable: any iterable
    :param chunksize: the size of the yielded lists
    :return: iterator
    :raises: RuntimeError if iterable is exhausted with some elements not yielded as lists
             (i.e. if the length of the iterable is not divisible by chunksize)

    :Example:

    .. doctest::

       >>> from pndniworkflows.utils import chunk
       >>> list(chunk(range(9), 3))
       [[0, 1, 2], [3, 4, 5], [6, 7, 8]]

    """
    out = []
    for x in iterable:
        out.append(x)
        if len(out) == chunksize:
            yield out
            out = []
    if len(out) > 0:
        raise RuntimeError('iterator length not divisible by chunksize')
    return


class UnaccountedBidsPropertiesError(Exception):
    pass


class InvariantViolationError(Exception):
    pass


class ColumnExistsError(Exception):
    pass


def combine_stats_files(bids_dir, validate, row_keys, invariants, outfile, strict=True,
                        index=None, ignore=None):
    """
    Search a bids directory for every file with suffix stats. Check
    that the properties of each stats file match invariants (i.e.::

        for k, v in invariants.items():
            assert bidsfile.get_entities()[k] == v

    Each row in the output tsv is a unique combination of row_keys.
    For example, if ``row_keys == ('subject',)`` then each row is a unqiue subject,
    if ``row_keys == ('subject', 'acquisition')`` then each row is a unique subject,
    acquisition combination, etc.

    if strict, every key in get_entities must be accounted for, either in row_keys or invariants (excluding "suffix")

    :param bids_dir: bids directory to search
    :param validate: validate bids directory (passed directly to :py:class:`BIDSLayout`
    :param row_keys: list of keys (bids parameters) to uniquely determine a row_key
    :param invariants: list dictionary of bids parameters that must be true (otherwise raise :py:class:`InvariantViolationError`)
    :param outfile: filelike object to write the combined tsv
    :param strict: If a found stats file has a bids paramter that isn't in either :py:obj:`row_keys` or :py:obj:`suffix`,
                   raise :py:class:`UnaccountedBidsPropertiesError`)
    :param index: passed to :py:func:`tsv_to_flat_dict`, is the key used to determine the row names of the input stats files
    :param ignore: passed to :py:func:`tsv_to_flat_dict`, container of keys to ignore while reading stats file

    :raises: :py:class:`UnaccountedBidsPropertiesError`, :py:class:`InvariantViolationError`, :py:class:`ColumnExistsError`

    :Example:

    Given a bids directory structure with::

        bids_dir
        ├──sub-1
        │  └──anat
        │     └──sub-1_stats.tsv
        │
        └──sub-2
           └──anat
              ├──sub-2_stats.tsv
              └──sub-2_acq-1_stats.tsv

    with ``sub-1_stats.tsv``:

    ===== ==== ====== ====
    index name volume mean
    ===== ==== ====== ====
    1     GM   10     20.0
    2     WM   5      30.0
    ===== ==== ====== ====

    with ``sub-2_stats.tsv``:

    ===== ==== ====== ====
    index name volume mean
    ===== ==== ====== ====
    1     GM   11     19.0
    2     WM   6      31.0
    ===== ==== ====== ====

    with ``sub-1_acq-1_stats.tsv``:

    ===== ==== ====== ====
    index name volume mean
    ===== ==== ====== ====
    1     GM   8      25.0
    2     WM   4      40.0
    ===== ==== ====== ====

    Then running:

    .. code-block:: python

       with open('outfile.tsv', 'w') as outfile:
           combine_stats_files('bids_dir', False, ('subject', 'acquisition'),
                               {'datatype': 'anat', 'extension': 'tsv'}, outfile,
                               index='name', ignore=['index'])

    produces ``sub-1_acq-1_stats.tsv``:

    ======= =========== ========= ======= ========= =======
    subject acquisition GM_volume GM_mean WM_volume WM_mean
    ======= =========== ========= ======= ========= =======
    1                   10        20.0    5         30.0
    2                   11        19.0    6         31.0
    2       1           8         25.0    4         40.0
    ======= =========== ========= ======= ========= =======

    """
    bids = layout.BIDSLayout(bids_dir, validate=validate)
    out = defaultdict(OrderedDict)
    for bidsfile in bids.get(suffix='stats'):
        ent = bidsfile.get_entities()
        unaccounted_ent_keys = set(ent.keys()) - (set(row_keys) | set(invariants.keys()) | {'suffix'})
        if strict and len(unaccounted_ent_keys) > 0:
            raise UnaccountedBidsPropertiesError(f'{unaccounted_ent_keys} not accounted for')
        for invk, invv in invariants.items():
            if ent[invk] != invv:
                raise InvariantViolationError(f'invariate {invk} = {invv} failed for {bidsfile.path}')
        assert ent['suffix'] == 'stats'
        outkey = tuple((ent.get(key, None) for key in row_keys))
        tsvdata = tsv_to_flat_dict(bidsfile.path, index=index, ignore=ignore)
        for tsvk, tsvv in tsvdata.items():
            if tsvk in out[outkey]:
                raise ColumnExistsError(f'Column name {tsvk} already exists. Row key {outkey}')
            out[outkey][tsvk] = tsvv
    # add row_keys to out values so they appear in the final tsv. also get list of all keys
    allkeys = []
    outkeyssorted = sorted(out.keys(), key=lambda x_: tuple((str(xt_) if xt_ is not None else '' for xt_ in x_)))
    for outkey in outkeyssorted:
        for tmpallkey in out[outkey].keys():
            if tmpallkey not in allkeys:
                allkeys.append(tmpallkey)
        for i, rowkey in enumerate(row_keys):
            if rowkey in out[outkey]:
                raise ColumnExistsError(f'row_key {rowkey} already in output entry {outkey}')
            if outkey[i] is not None:
                if outkey[i] == '':
                    # I'm not sure it's possible to get here. for example ...acq-_... in a bids filename
                    # seems to result in acquisition=None, not ''
                    raise ValueError("row_key values of '' are not supported")
                out[outkey][rowkey] = outkey[i]
    writer = csv.DictWriter(outfile, fieldnames=list(row_keys) + allkeys, delimiter='\t')
    writer.writeheader()
    for outkey in outkeyssorted:
        writer.writerow(out[outkey])


def tsv_to_flat_dict(tsvfile, index=None, ignore=None):
    """Read a tsv file and convert it to a flattend dictionary

    :param tsvfile: input file
    :param index: name of column specifying row names
    :param ignore: container of column names to ignore
    :return: :py:obj:`OrderedDict` with keys given by rowname_colname, where rowname is
             the table item in the column given by index

    :Examples:

    :py:obj:`tsvfile` contents

    ==== ==== ==== ====
    col1 col2 col3 col4
    ==== ==== ==== ====
    a    1    2    3
    b    4    5    6
    ==== ==== ==== ====

    .. testsetup::

       import tempfile
       from pndniworkflows.utils import tsv_to_flat_dict
       testdata = [['col1', 'col2', 'col3', 'col4'],
                   [   'a',      1,      2,      3],
                   [   'b',      4,      5,      6]]
       with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
          f.write('\\n'.join(['\\t'.join([str(c) for c in row]) for row in testdata]))
          tsvfile = f.name

    .. doctest::

       >>> tsv_to_flat_dict(tsvfile)
       OrderedDict([('a_col2', '1'), ('a_col3', '2'), ('a_col4', '3'), ('b_col2', '4'), ('b_col3', '5'), ('b_col4', '6')])
       >>> tsv_to_flat_dict(tsvfile, index='col2')
       OrderedDict([('1_col1', 'a'), ('1_col3', '2'), ('1_col4', '3'), ('4_col1', 'b'), ('4_col3', '5'), ('4_col4', '6')])
       >>> tsv_to_flat_dict(tsvfile, index='col2', ignore=['col4'])
       OrderedDict([('1_col1', 'a'), ('1_col3', '2'), ('4_col1', 'b'), ('4_col3', '5')])

    .. testcleanup::

       import os
       os.remove(tsvfile)


    """
    out = OrderedDict()
    with open(tsvfile, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)
        if index is not None:
            index_ind = header.index(index)
        else:
            index_ind = 0
        if ignore is None:
            ignore = {}
        if header[index_ind] in ignore:
            raise ValueError('index cannot be an element of ignore')
        for row in reader:
            for colind, rowitem in enumerate(row):
                if colind == index_ind or header[colind] in ignore:
                    continue
                outkey = f'{row[index_ind]}_{header[colind]}'
                if outkey in out:
                    raise RuntimeError('Duplicate keys while flattening tsv file')
                out[outkey] = rowitem
    return out
