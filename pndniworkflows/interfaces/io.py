from nipype.interfaces.base import (Directory,
                                    File,
                                    TraitedSpec,
                                    traits,
                                    isdefined,
                                    BaseInterfaceInputSpec,
                                    SimpleInterface)
from nipype.interfaces import Rename
from pathlib import Path
from ..utils import write_labels, chunk, combine_stats_files, get_BIDSLayout_with_conf
import shutil
import csv
import errno


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


class WriteBIDSFile(SimpleInterface):
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
        self._results['out_file'] = str(outfull)
        shutil.copy(self.inputs.in_file, outfull)
        if isdefined(self.inputs.labelinfo):
            args['extension'] = 'tsv'
            args['presuffix'] = args['suffix']
            args['suffix'] = 'labels'
            outtsv = self.__make_and_prepare_bids_file(args)
            self._results['out_labelfile'] = str(outtsv)
            write_labels(str(outtsv), self.inputs.labelinfo)
        return runtime

    def __make_and_prepare_bids_file(self, bidsargs):
        b = get_BIDSLayout_with_conf(self.inputs.out_dir, validate=False)
        p = b.build_path(bidsargs, strict=True, validate=False)
        if p is None:
            raise RuntimeError('BIDSLayout was unable to build a path with parameters ' + ', '.join([f'{key}: {val}' for key, val in bidsargs.items()]))
        outfull = (Path(self.inputs.out_dir) / p).resolve()
        if outfull.exists():
            raise RuntimeError(f'{str(outfull)} already exists')
        outfull.parent.mkdir(parents=True, exist_ok=True)
        return outfull


class WriteFSLStatsInputSpec(BaseInterfaceInputSpec):
    statnames = traits.List(trait=traits.Str(), mandatory=True, desc='list of column names')
    labels = traits.Dict(key_trait=traits.Int(), value_trait=traits.Str(), mandatory=True,
                         desc='dictionary mapping indexes to label names')
    data = traits.List(mandatory=True, desc='A list of data values. The length must be the '
                                            'length of statnames times the maximum index in label. '
                                            'Each element corresponds to a statname/label combination.')


class WriteFSLStatsOutputSpec(TraitedSpec):
    out_tsv = traits.File(exists=True)


class WriteFSLStats(SimpleInterface):
    """Write a list of data to a TSV file. Designed to be used with ImageStats

    Example:

    >>> write = WriteFSLStats(statnames=['mean', 'std'], labels={1: 'GM', 2: 'WM'}, data=[1, 2, 3, 4])
    >>> r = write.run()

    Will produce :py:obj:`r.outputs.out_tsv` containing

    ===== ==== ==== ===
    index name mean std
    ===== ==== ==== ===
    1     GM   1    2
    2     WM   3    4
    ===== ==== ==== ===

    If not all labels are specified, then the corresponding data must be zero.

    >>> write = WriteFSLStats(statnames=['mean', 'std'], labels={1: 'GM', 3: 'CSF'}, data=[1, 2, 0, 0, 3, 4])
    >>> r = write.run()

    Will produce :py:obj:`r.outputs.out_tsv` containing

    ===== ==== ==== ===
    index name mean std
    ===== ==== ==== ===
    1     GM   1    2
    3     CSF  3    4
    ===== ==== ==== ===

    However, the following will fail

    >>> write = WriteFSLStats(statnames=['mean', 'std'], labels={1: 'GM', 3: 'CSF'}, data=[1, 2, 3, 4])
    >>> r = write.run()

    """

    input_spec = WriteFSLStatsInputSpec
    output_spec = WriteFSLStatsOutputSpec

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
        self._results['out_tsv'] = str(outfile.resolve())
        return runtime


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


class CombineStats(SimpleInterface):
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
        self._results['out_tsv'] = str(outfile.resolve())
        return runtime


class WriteFileInputSpec(BaseInterfaceInputSpec):
    string = traits.Str(mandatory=True)
    newline = traits.Either(traits.Str, None, default=None, usedefault=True)
    out_file = File()


class WriteFileOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output file name')


class WriteFile(SimpleInterface):
    """Write a string to a file"""

    input_spec = WriteFileInputSpec
    output_spec = WriteFileOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.out_file):
            out_file = Path(self.inputs.out_file).resolve()
        else:
            out_file = Path('outputfile.txt').resolve()
        with open(out_file, 'w', newline=self.inputs.newline) as f:
            f.write(self.inputs.string)
        self._results['out_file'] = str(out_file)
        return runtime


class MismatchedExtensionError(Exception):
    pass


class RenameAndCheckExtension(Rename):
    """subclass of Rename that throws an error if the file extension is not preserved
    """

    def _run_interface(self, runtime):
        super()._run_interface(runtime)
        if Path(self.inputs.in_file).suffix != Path(self._results['out_file']).suffix:
            raise MismatchedExtensionError(f'{self.inputs.in_file} and {self._results["out_file"]} have different extensions')
        return runtime


class ExportFileInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='Input file name')
    out_file = File(exists=False, desc='Output file name')
    check_extension = traits.Bool(False, desc='Ensure that the input and output file extensions match')
    clobber = traits.Bool(False, desc='Permit overwriting existing files')


class ExportFileOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output file name')


class ExportFile(SimpleInterface):
    input_spec = ExportFileInputSpec
    output_spec = ExportFileOutputSpec

    def _run_interface(self, runtime):
        in_file = Path(self.inputs.in_file)
        out_file = Path(self.inputs.out_file)
        if not self.inputs.clobber and out_file.exists():
            raise FileExistsError(errno.EEXIST, f'File {out_file} exists')
        if self.inputs.check_extension and in_file.suffix != out_file.suffix:
            raise MismatchedExtensionError(f'{in_file} and {out_file} have different extensions')
        shutil.copy(str(in_file), str(out_file))
        self._results['out_file'] = self.inputs.out_file
        return runtime
