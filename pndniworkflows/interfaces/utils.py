from nipype.interfaces.base import (traits,
                                    isdefined,
                                    File,
                                    TraitedSpec,
                                    BaseInterfaceInputSpec,
                                    SimpleInterface,
                                    StdOutCommandLine,
                                    StdOutCommandLineInputSpec)
from nipype.algorithms.misc import Gunzip
from pndniworkflows.utils import Points, csv2tsv
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


class ConvertPointsInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True,
                   desc='Input file.')
    in_format = traits.Enum('tsv', 'ants', 'minc',
                            desc="""Input file format.

"tsv": a TSV file with "x", "y", "z", and "index"
        columns (of types float, float, float, and int, respectively). All other
        columns will be ignored

"ants": A CSV file with "x", "y", "z", and "index"
        columns (of types float, float, float, and int, respectively). All other
        columns will be ignored. The x and y columns will be multiplied by -1.0
        (ants uses LPS while this class uses RAS).

"minc": a '`minc tag file <https://en.wikibooks.org/wiki/MINC/SoftwareDevelopment/Tag_file_format_reference>`_'.
        In this case, we assume each point has 7 parameters, and that the text label is quoted. Therefore
        it is more restrictive than the linked specification. All information besides x, y, z, and label
        are ignored.
""")
    out_format = traits.Enum('tsv', 'ants', 'minc',
                             desc='Output type.')


class ConvertPointsOutputSpec(TraitedSpec):
    out_file = File(exists=True,
                    desc='Output file.')


class ConvertPoints(SimpleInterface):
    """Convert a points file. Formats determined by which input/output
    traits are used.
    """
    input_spec = ConvertPointsInputSpec
    output_spec = ConvertPointsOutputSpec

    def _run_interface(self, runtime):
        if self.inputs.out_format == 'tsv':
            ext = '.tsv'
        elif self.inputs.out_format == 'ants':
            ext = '.csv'
        elif self.inputs.out_format == 'minc':
            ext = '.tag'
        out = Path(Path(self.inputs.in_file).with_suffix(ext).name).resolve()
        if out.exists():
            raise RuntimeError(f'File {out} exists.')
        if self.inputs.in_format == 'tsv':
            points = Points.from_tsv(self.inputs.in_file)
        elif self.inputs.in_format == 'ants':
            points = Points.from_ants_csv(self.inputs.in_file)
        elif self.inputs.in_format == 'minc':
            points = Points.from_minc_tag(self.inputs.in_file)
        else:
            raise ValueError('Unsupported input format. This should be inpossible')
        if self.inputs.out_format == 'tsv':
            points.to_tsv(out)
        elif self.inputs.out_format == 'ants':
            points.to_ants_csv(out)
        elif self.inputs.out_format == 'minc':
            points.to_minc_tag(out)
        else:
            raise ValueError('Unsupported output format. This should be inpossible')
        self._results['out_file'] = out
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
