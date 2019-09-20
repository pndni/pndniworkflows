from nipype.interfaces.base import (traits,
                                    File,
                                    TraitedSpec,
                                    BaseInterface,
                                    BaseInterfaceInputSpec)
from nipype.algorithms.misc import Gunzip
import csv
import re
import os
from pndniworkflows.utils import Points
from pathlib import Path


class ItemInputSpec(BaseInterfaceInputSpec):
    in_list = traits.List(trait=traits.Any(),
                          desc='List of length 1')


class ItemOutputSpec(TraitedSpec):
    out_item = traits.Any(desc='The item in the list (i.e. ``in_list[0]``)')


class Item(BaseInterface):
    """Extract the first item from a list, raising an error if the
    length of the list is not exactly one."""
    input_spec = ItemInputSpec
    output_spec = ItemOutputSpec

    def _run_interface(self, runtime):
        in_list = self.inputs.in_list
        if len(in_list) != 1:
            raise ValueError('Length of list does not equal 1')
        self.__out_item_tmp = in_list[0]
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_item'] = self.__out_item_tmp
        return outputs


class MergeDictionariesInputSpec(BaseInterfaceInputSpec):
    in1 = traits.Dict()
    in2 = traits.Dict()


class MergeDictionariesOutputSpec(TraitedSpec):
    out = traits.Dict()


class MergeDictionaries(BaseInterface):
    """Merge two dictionaries, raising an error if they have keys in common
    """
    input_spec = MergeDictionariesInputSpec
    output_spec = MergeDictionariesOutputSpec

    def _run_interface(self, runtime):
        if len(set(self.inputs.in1.keys()).intersection(set(self.inputs.in2.keys()))) > 0:
            raise ValueError('Dictionaries must not have common keys')
        self.__out_dict_tmp = {**self.inputs.in1, **self.inputs.in2}
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out'] = self.__out_dict_tmp
        return outputs


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


class GetInputSpec(BaseInterfaceInputSpec):
    dictionary = traits.Dict(mandatory=True)
    key = traits.Any(mandatory=True)


class GetOutputSpec(TraitedSpec):
    item = traits.Any()


class Get(BaseInterface):
    """extract value from dictionary
    ``item = dictionary[key]``
    """
    input_spec = GetInputSpec
    output_spec = GetOutputSpec

    def _run_interface(self, runtime):
        self.__out_item_tmp = self.inputs.dictionary[self.inputs.key]
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['item'] = self.__out_item_tmp
        return outputs


class DictToStringInputSpec(BaseInterfaceInputSpec):
    dictionary = traits.Dict(mandatory=True)
    keys = traits.Dict(mandatory=True,
                       desc='keys to use to construct string. the values in this dictionary will appear in the output string')


class DictToStringOutputSpec(TraitedSpec):
    out = traits.Str()


class DictToString(BaseInterface):
    """Equivalent to

    .. code-block:: python

       '_'.join(('{}-{}'.format(keyval, dictionary[key])
                                for key, keyval in keys.items()
                                if key in dictionary))

    """
    input_spec = DictToStringInputSpec
    output_spec = DictToStringOutputSpec

    def _run_interface(self, runtime):
        self.__out_str_tmp = '_'.join(('{}-{}'.format(keyval, self.inputs.dictionary[key])
                                       for key, keyval in self.inputs.keys.items()
                                       if key in self.inputs.dictionary))
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out'] = self.__out_str_tmp
        return outputs
#
#
# class NiftiTypeInputSpec(BaseInterfaceInputSpec):
#     in_file = File(exists=True)
#
#
# class NiftiTypeOutputSpec(TraitedSpec):
#     write_byte = traits.Bool()
#     write_short = traits.Bool()
#     write_int = traits.Bool()
#     write_float = traits.Bool()
#     write_double = traits.Bool()
#     write_signed = traits.Bool()
#     write_unsigned = traits.Bool()
#
#
# class NiftyType(BaseInterface):
#     input_spec = NiftiTypeInputSpec
#     output_spec = NiftiTypeOutputSpec
#     typemap = {'b': 'write_byte',
#                'h': 'write_short',
#                'i': 'write_int',
#                'f': 'write_float',
#                'd': 'write_double'}
#
#     def _run_interface(self, runtime):
#         t = nibabel.load(self.inputs.in_file).get_data_dtype()
#         out = self._outputs().get()
#         for k in out.keys():
#             out[k] = False
#         if t.kind == 'u':
#             out['write_unsigned'] = True
#         else:
#             out['write_signed'] = True
#         out[self.typemap[t.char.lower()]] = True
#         self.__output_type_flags = out
#         return runtime
#
#     def _list_outputs(self):
#         return self.__output_type_flags


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


class ConvertPoints(BaseInterface):
    """Convert a points file. Formats determined by which input/output
    traits are used.
    """
    input_spec = ConvertPointsInputSpec
    output_spec = ConvertPointsOutputSpec

    def _run_interface(self, runtime):
        out = self._list_outputs()['out_file']
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
        return runtime

    def _list_outputs(self):
        out = self._outputs().get()
        if self.inputs.out_format == 'tsv':
            ext = '.tsv'
        elif self.inputs.out_format == 'ants':
            ext = '.csv'
        elif self.inputs.out_format == 'minc':
            ext = '.tag'
        out['out_file'] = Path(Path(self.inputs.in_file).with_suffix(ext).name).resolve()
        return out
