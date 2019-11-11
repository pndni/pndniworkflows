from nipype.interfaces.base import (traits,
                                    isdefined,
                                    File,
                                    TraitedSpec,
                                    BaseInterfaceInputSpec,
                                    SimpleInterface,
                                    StdOutCommandLine,
                                    StdOutCommandLineInputSpec)
from nipype.algorithms.misc import Gunzip
from pndniworkflows.utils import csv2tsv, cutimage
from pathlib import Path


class ItemInputSpec(BaseInterfaceInputSpec):
    in_list = traits.List(trait=traits.Any(),
                          desc='List of length 1')


class ItemOutputSpec(TraitedSpec):
    out_item = traits.Any(desc='The item in the list (i.e. ``in_list[0]``)')


class Item(SimpleInterface):
    """Extract the first item from a list, raising an error if the
    length of the list is not exactly one."""
    input_spec = ItemInputSpec
    output_spec = ItemOutputSpec

    def _run_interface(self, runtime):
        in_list = self.inputs.in_list
        if len(in_list) != 1:
            raise ValueError('Length of list does not equal 1')
        self._results['out_item'] = in_list[0]
        return runtime


class MergeDictionariesInputSpec(BaseInterfaceInputSpec):
    in1 = traits.Dict()
    in2 = traits.Dict()


class MergeDictionariesOutputSpec(TraitedSpec):
    out = traits.Dict()


class MergeDictionaries(SimpleInterface):
    """Merge two dictionaries, raising an error if they have keys in common
    """
    input_spec = MergeDictionariesInputSpec
    output_spec = MergeDictionariesOutputSpec

    def _run_interface(self, runtime):
        if len(set(self.inputs.in1.keys()).intersection(set(self.inputs.in2.keys()))) > 0:
            raise ValueError('Dictionaries must not have common keys')
        self._results['out'] = {**self.inputs.in1, **self.inputs.in2}
        return runtime


class GunzipOrIdent(Gunzip):
    """
    like Gunzip, but if input file does not end in .gz
    just copy the file
    """

    def _run_interface(self, runtime):
        import shutil
        if self.inputs.in_file[-3:].lower() == '.gz':
            runtime = super()._run_interface(runtime)
        else:
            shutil.copyfile(self.inputs.in_file, self._gen_output_file_name())
        return runtime


class GzipInputSpec(StdOutCommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', position=0, desc='Input file')


class GzipOutputSpec(TraitedSpec):
    out_file = File(desc='Output file')


class Gzip(StdOutCommandLine):
    input_spec = GzipInputSpec
    output_spec = GzipOutputSpec
    _cmd = 'gzip --to-stdout'

    def _gen_outfilename(self):
        return Path(Path(self.inputs.in_file).name + '.gz').resolve()

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class GetInputSpec(BaseInterfaceInputSpec):
    dictionary = traits.Dict(mandatory=True)
    key = traits.Any(mandatory=True)


class GetOutputSpec(TraitedSpec):
    item = traits.Any()


class Get(SimpleInterface):
    """extract value from dictionary
    ``item = dictionary[key]``
    """
    input_spec = GetInputSpec
    output_spec = GetOutputSpec

    def _run_interface(self, runtime):
        self._results['item'] = self.inputs.dictionary[self.inputs.key]
        return runtime


class DictToStringInputSpec(BaseInterfaceInputSpec):
    dictionary = traits.Dict(mandatory=True)
    keys = traits.Dict(mandatory=True,
                       desc='keys to use to construct string. the values in this dictionary will appear in the output string')


class DictToStringOutputSpec(TraitedSpec):
    out = traits.Str()


class DictToString(SimpleInterface):
    """Equivalent to

    .. code-block:: python

       '_'.join(('{}-{}'.format(keyval, dictionary[key])
                                for key, keyval in keys.items()
                                if key in dictionary))

    """
    input_spec = DictToStringInputSpec
    output_spec = DictToStringOutputSpec

    def _run_interface(self, runtime):
        self._results['out'] = '_'.join(('{}-{}'.format(keyval, self.inputs.dictionary[key])
                                         for key, keyval in self.inputs.keys.items()
                                         if key in self.inputs.dictionary))
        return runtime


class Csv2TsvInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='Input CSV file', mandatory=True)
    out_file = File(desc='Output TSV file')
    header = traits.ListStr(desc='Header to add to output file')


class Csv2TsvOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output TSV file')


class Csv2Tsv(SimpleInterface):
    input_spec = Csv2TsvInputSpec
    output_spec = Csv2TsvOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.out_file):
            out_file = self.inputs.out_file
        else:
            out_file = Path(Path(self.inputs.in_file).stem + '.tsv').resolve()
        if isdefined(self.inputs.header):
            header = self.inputs.header
        else:
            header = None
        csv2tsv(self.inputs.in_file, out_file, header=header)
        self._results['out_file'] = out_file
        return runtime


class CutImageInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, desc='Input file to cut', mandatory=True)
    points_file = File(exists=True, desc='TSV file with points either indicating box or cutting plane', mandatory=True)
    neckonly = traits.Bool(True, desc='If true, cut off image below inferior-most point. Otherwise, cut to box around points')


class CutImageOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Cut file')


class CutImage(SimpleInterface):
    input_spec = CutImageInputSpec
    output_spec = CutImageOutputSpec

    def _run_interface(self, runtime):
        outfile = cutimage(self.inputs.in_file,
                           self.inputs.points_file,
                           self.inputs.neckonly)
        self._results['out_file'] = outfile
        return runtime
