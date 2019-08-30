from nipype.pipeline import engine as pe
from nipype import IdentityInterface, Function
from nipype.interfaces.fsl import ImageStats
from collections import namedtuple
import csv
from pathlib import Path
from . import utils
from .interfaces.io import WriteTSV
from itertools import product


StatDesc = namedtuple('StatDesc', ['flag', 'names'])


STATS = {'robustminmax': StatDesc('-r', ['robust_min', 'robust_max']),
         'minmax': StatDesc('-R', ['min', 'max']),
         'meanentropy': StatDesc('-e', ['mean_entropy']),
         'meanentropy_nz': StatDesc('-E', ['mean_entropy_nonzero_voxels']),
         'volume': StatDesc('-v', ['number_voxels', 'volume']),
         'volume_nz': StatDesc('-V', ['number_nonzero_voxels', 'volume_nonzero_voxels']),
         'mean': StatDesc('-m', ['mean']),
         'mean_nz': StatDesc('-M', ['mean_nonzero_voxels']),
         'std': StatDesc('-s', ['standard_deviation']),
         'std_nz': StatDesc('-S', ['standard_deviation_nonzero_voxels'])}


def image_stats_wf(stat_keys, labels, name):
    """Create a workflow to calculate image statistics using fslstats
    
    :param stat_keys: list of keys indicating which statistics to calculate.
                      Can be any of the keys of :py:const:`pndniworkflows.postprocessing.STATS`.
    :param labels: :py:class:`list` of :py:class:`OrderedDict`, one for each label. Each
                   :py:class:`OrderedDict` must have an "index" field.
                   (e.g. ``[OrderedDict(index=1, name='Brain'), OrderedDict(index=2, name='WM')]``)
    :param name: The name of the workflow

    :return: A :py:mod:`nipype` workflow
    
    Workflow inputs/outputs
    
    :param inputspec.in_file: file on which to compute statistics
    :param inputspec.index_mask_file: label file indicating the ROIs of
                                      in_file in which to compute
                                      statistics

    :param outputspec.out_file: output tsv file

    """
    wf = pe.Workflow(name)
    stats = [STATS[key] for key in stat_keys]
    op_string = ' '.join((stat.flag for stat in stats))
    inputspec = pe.Node(IdentityInterface(['in_file', 'index_mask_file']), 'inputspec')
    imagestats = pe.Node(ImageStats(op_string=op_string), 'imagestats')
    write = pe.Node(WriteTSV(), 'write')
    header = []
    for stat in stats:
        header += stat.names
    write.inputs.statnames = header
    write.inputs.labels = utils.labels2dict(labels, 'name')
    outputspec = pe.Node(IdentityInterface(['out_file']), 'outputspec')
    wf.connect([(inputspec, imagestats, [('in_file', 'in_file'),
                                         ('index_mask_file', 'index_mask_file')]),
                (imagestats, write, [('out_stat', 'data')]),
                (write, outputspec, [('out_tsv', 'out_file')])])
    return wf
