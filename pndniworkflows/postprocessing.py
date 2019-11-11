from nipype.pipeline import engine as pe
from nipype import IdentityInterface
from nipype.interfaces.fsl import ImageStats
from collections import namedtuple
from . import utils
from .interfaces.io import WriteFSLStats
from .interfaces.pndni_utils import Stats
from .interfaces.utils import Zipper


StatDesc = namedtuple('StatDesc', ['flag', 'names', 'fsl'])


STATS = {'robustminmax': StatDesc('-r', ['robust_min', 'robust_max'], True),
         'minmax': StatDesc('-R', ['min', 'max'], True),
         'meanentropy': StatDesc('-e', ['mean_entropy'], True),
         'meanentropy_nz': StatDesc('-E', ['mean_entropy_nonzero_voxels'], True),
         'volume': StatDesc('-v', ['number_voxels', 'volume'], True),
         'volume_nz': StatDesc('-V', ['number_nonzero_voxels', 'volume_nonzero_voxels'], True),
         'mean': StatDesc('-m', ['mean'], True),
         'mean_nz': StatDesc('-M', ['mean_nonzero_voxels'], True),
         'std': StatDesc('-s', ['standard_deviation'], True),
         'std_nz': StatDesc('-S', ['standard_deviation_nonzero_voxels'], True),
         'median': StatDesc('--median', ['median'], False),
         'skew': StatDesc('--skew', ['skew'], False),
         'kurtosis': StatDesc('--kurtosis', ['kurtosis'], False)}


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
    fsl_op_string = ' '.join((stat.flag for stat in stats if stat.fsl))
    stats_op_string = ' '.join((stat.flag for stat in stats if not stat.fsl))
    inputspec = pe.Node(IdentityInterface(['in_file', 'index_mask_file']), 'inputspec')
    if fsl_op_string:
        fslimagestats = pe.Node(ImageStats(op_string=fsl_op_string), 'fslimagestats')
    if stats_op_string:
        statsimagestats = pe.Node(Stats(op_string=stats_op_string), 'statsimagestats')
    write = pe.Node(WriteFSLStats(), 'write')
    fsl_header = []
    stats_header = []
    for stat in stats:
        if stat.fsl:
            fsl_header += stat.names
        else:
            stats_header += stat.names
    header = fsl_header + stats_header
    write.inputs.statnames = header
    write.inputs.labels = utils.labels2dict(labels, 'name')
    outputspec = pe.Node(IdentityInterface(['out_file']), 'outputspec')
    if fsl_op_string:
        wf.connect([(inputspec, fslimagestats, [('in_file', 'in_file'),
                                                ('index_mask_file', 'index_mask_file')])])
    if stats_op_string:
        wf.connect([(inputspec, statsimagestats, [('in_file', 'in_file'),
                                                  ('index_mask_file', 'index_mask_file')])])
    if fsl_op_string and stats_op_string:
        zipper = pe.Node(Zipper(chunksize1=len(fsl_header), chunksize2=len(stats_header)), 'zipper')
        wf.connect(fslimagestats, 'out_stat', zipper, 'list1')
        wf.connect(statsimagestats, 'out_stat', zipper, 'list2')
        wf.connect(zipper, 'out_list', write, 'data')
    elif fsl_op_string:
        wf.connect(fslimagestats, 'out_stat', write, 'data')
    elif stats_op_string:
        wf.connect(statsimagestats, 'out_stat', write, 'data')
    wf.connect(write, 'out_tsv', outputspec, 'out_file')
    return wf
