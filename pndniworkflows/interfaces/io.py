from nipype.interfaces.base import (Directory,
                                    File,
                                    TraitedSpec,
                                    traits,
                                    isdefined,
                                    BaseInterface,
                                    BaseInterfaceInputSpec)
from pathlib import Path
from ..utils import get_bids_patterns, write_labels, chunk, combine_stats_files
from bids import BIDSLayout
import shutil
import csv


class WriteBIDSFileInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True, desc='input file')
    out_dir = Directory(exists=True, mandatory=True, desc='output directory (bids root)')
    labelinfo = traits.List(desc=':py:obj:`list` of :py:obj:`dict`. If specified, will be written '
                                 'to a tsv file corresponding to the output bids file using '
                                 ':py:func:`utils.write_labels`')
    bidsparams = traits.DictStrAny(mandatory=True,
                                   desc='Bids parameters to be passed to :py:meth:`BIDSLayout.build_path`. '
                                        'Must not include "extension", which will be determined from :py:obj:`in_file`')
    # session = traits.Str()
    # acquisition = traits.Str()
    # contrast = traits.Str()
    # reconstruction = traits.Str()
    # space = traits.Str()
    # label = traits.Str()
    # skullstripped = traits.Str()
    # description = traits.Str()
    # from_ = traits.Str()
    # to = traits.Str()
    # mode = traits.Str()
    # suffix = traits.Str()
    # map_ = traits.Str()


class WriteBIDSFileOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output file name')
    out_labelfile = File(desc='output label file name')


class WriteBIDSFile(BaseInterface):
    """Copy the input file to a file with a bids-style name"""

    input_spec = WriteBIDSFileInputSpec
    output_spec = WriteBIDSFileOutputSpec

    def _run_interface(self, runtime):
        if 'extension' in self.inputs.bidsparams.keys():
            raise ValueError('"extension" must not be specified. It is determined from the input file')
        args = {'extension': ''.join(Path(self.inputs.in_file).suffixes)[1:]}
        for key, val in self.inputs.bidsparams.items():
            args[key] = val
        outfull = self.__make_and_prepare_bids_file(args)
        self.__makebidspath_output_tmp = str(outfull)
        shutil.copy(self.inputs.in_file, outfull)
        self.__makebidspath_output_label_tmp = None
        if isdefined(self.inputs.labelinfo):
            args['extension'] = 'tsv'
            outtsv = self.__make_and_prepare_bids_file(args)
            self.__makebidspath_output_label_tmp = str(outtsv)
            write_labels(str(outtsv), self.inputs.labelinfo)
        return runtime

    def __make_and_prepare_bids_file(self, bidsargs):
        b = BIDSLayout(self.inputs.out_dir, validate=False)
        p = b.build_path(bidsargs, path_patterns=get_bids_patterns(), strict=True)
        if p is None:
            raise RuntimeError('BIDSLayout was unable to build a path with parameters ' + ', '.join([f'{key}: {val}' for key, val in bidsargs.items()]))
        outfull = (Path(self.inputs.out_dir) / p).resolve()
        if outfull.exists():
            raise RuntimeError(f'{str(outfull)} already exists')
        outfull.parent.mkdir(parents=True, exist_ok=True)
        return outfull

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.__makebidspath_output_tmp
        if self.__makebidspath_output_label_tmp is not None:
            outputs['out_labelfile'] = self.__makebidspath_output_label_tmp
        return outputs


class WriteTSVInputSpec(BaseInterfaceInputSpec):
    statnames = traits.List(trait=traits.Str(), mandatory=True, desc='list of column names')
    labels = traits.Dict(key_trait=traits.Int(), value_trait=traits.Str(), mandatory=True,
                         desc='dictionary mapping indexes to label names')
    data = traits.List(mandatory=True, desc='A list of data values. The length must be the '
                                            'length of statnames times the maximum index in label. '
                                            'Each element corresponds to a statname/label combination.')


class WriteTSVOutputSpec(TraitedSpec):
    out_tsv = traits.File(exists=True)


class WriteTSV(BaseInterface):
    """Write a list of data to a TSV file. Designed to be used with ImageStats
    
    Example:

    >>> write = WriteTSV(statnames=['mean', 'std'], labels={1: 'GM', 2: 'WM'}, data=[1, 2, 3, 4])
    >>> r = write.run()

    Will produce :py:obj:`r.outputs.out_tsv` containing
    
    ===== ==== ==== ===
    index name mean std
    ===== ==== ==== ===
    1     GM   1    2
    2     WM   3    4
    ===== ==== ==== ===
    
    If not all labels are specified, then the corresponding data must be zero.

    >>> write = WriteTSV(statnames=['mean', 'std'], labels={1: 'GM', 3: 'CSF'}, data=[1, 2, 0, 0, 3, 4])
    >>> r = write.run()

    Will produce :py:obj:`r.outputs.out_tsv` containing
    
    ===== ==== ==== ===
    index name mean std
    ===== ==== ==== ===
    1     GM   1    2
    3     CSF  3    4
    ===== ==== ==== ===
    
    However, the following will fail

    >>> write = WriteTSV(statnames=['mean', 'std'], labels={1: 'GM', 3: 'CSF'}, data=[1, 2, 3, 4])
    >>> r = write.run()

    """

    input_spec = WriteTSVInputSpec
    output_spec = WriteTSVOutputSpec

    def _run_interface(self, runtime):
        outfile = Path('out.tsv')
        if outfile.exists():
            raise RuntimeError(f'{str(outfile)} exists! exiting')
        header = ['index', 'name'] + self.inputs.statnames
        datalength = max(self.inputs.labels.keys()) * len(self.inputs.statnames)
        if len(self.inputs.data) != datalength:
            raise ValueError(f'length of data {len(self.inputs.data)} does not match expected {datalength}')
        with open(outfile, 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(header)
            for index, datarow in enumerate(chunk(self.inputs.data, len(self.inputs.statnames)), start=1):
                if index not in self.inputs.labels.keys():
                    if len(list(filter(lambda dr: dr != 0, datarow))) > 0:
                        raise ValueError('Undefined label has nonzero data')
                else:
                    writer.writerow([index, self.inputs.labels[index]] + datarow)
        self.__out_tsv_tmp = str(outfile.resolve())
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_tsv'] = self.__out_tsv_tmp
        return outputs


class CombineStatsInputSpec(BaseInterfaceInputSpec):
    bids_dir = traits.Directory(exists=True, mandatory=True)
    validate = traits.Bool(default=True, usedefault=True)
    row_keys = traits.ListStr(mandatory=True)
    invariants = traits.DictStrAny()
    strict = traits.Bool(default=True, usedefault=True)
    index = traits.Str()
    ignore = traits.Either(traits.ListStr,
                           traits.Set(trait=traits.Str),
                           traits.Tuple(trait=traits.Str))


class CombineStatsOutputSpec(TraitedSpec):
    out_tsv = traits.File(exists=True)


class CombineStats(BaseInterface):
    """interface wrapping :py:func:`pndniworkflows.utils.combine_stats_files`. See that function for details"""

    input_spec = CombineStatsInputSpec
    output_spec = CombineStatsOutputSpec

    def _run_interface(self, runtime):
        outfile = Path('combined.tsv')
        if outfile.exists():
            raise RuntimeError(f'{outfile} exists')
        invariants = self.inputs.invariants if isdefined(self.inputs.invariants) else {}
        index = self.inputs.index if isdefined(self.inputs.index) else None
        ignore = self.inputs.ignore if isdefined(self.inputs.ignore) else None
        with open(outfile, 'w') as f:
            combine_stats_files(self.inputs.bids_dir,
                                self.inputs.validate,
                                self.inputs.row_keys,
                                invariants,
                                f,
                                strict=self.inputs.strict,
                                index=index,
                                ignore=ignore)
        self.__out_tsv_tmp = str(outfile.resolve())
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_tsv'] = self.__out_tsv_tmp
        return outputs
