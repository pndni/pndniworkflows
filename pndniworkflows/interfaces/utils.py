from nipype.interfaces.base import (traits,
                                    File,
                                    TraitedSpec,
                                    BaseInterface,
                                    BaseInterfaceInputSpec)
from nipype.algorithms.misc import Gunzip
import csv
import re
import os


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


class Minc2AntsPointsInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True,
                   desc='`Format reference <https://en.wikibooks.org/wiki/MINC/SoftwareDevelopment/Tag_file_format_reference>`_')
    flipxy = traits.Bool(False,
                         desc='Whether to negate the output x and y values. This is usually what you want '
                              'as ANTS uses ITK, which operates in LPS coordinates (when ANTS loads a '
                              'Nifti file it converts the affine matrix to LPS, so your ANTS points file '
                              ' should be in LPS).')


class Minc2AntsPointsOutputSpec(TraitedSpec):
    out_file = File(exists=True,
                    desc='CSV file with columns x,y,z,weight,structID,patientID,label,t')


class Minc2AntsPoints(BaseInterface):
    """Convert an MNI points
    file to an ANTS points file
    """
    input_spec = Minc2AntsPointsInputSpec
    output_spec = Minc2AntsPointsOutputSpec

    def _run_interface(self, runtime):
        out = self._list_outputs()['out_file']
        with open(self.inputs.in_file, 'r') as f, open(out, 'w') as fout:
            writer = csv.writer(fout, delimiter=',')
            writer.writerow(['x', 'y', 'z', 'weight', 'structID', 'patientID', 'label', 't'])
            contents = f.read()
            # remove comments
            contents = re.sub('[#%][^\n]*\n', '\n', contents)
            match = re.match(r'MNI Tag Point File\n+Volumes = [12];\n+\s*Points =([^;]*);', contents)
            pointsstr = match.group(1)
            points = pointsstr.split()
            npoints = len(points) // 7
            if npoints != len(points) / 7.0:
                raise RuntimeError('MNI Tags file must have 7 fields per point')
            for i in range(npoints):
                rowitems = points[i * 7:(i + 1) * 7]
                rowfloats = rowitems[:6]
                label = rowitems[6]
                rowfloats = [float(tmp) for tmp in rowfloats]
                if self.inputs.flipxy:
                    rowfloats[0] *= -1
                    rowfloats[1] *= -1
                if label[0] != '"' or label[-1] != '"':
                    raise RuntimeError("label must be surrounded by quotes")
                label = label[1:-1]
                writer.writerow(rowfloats + [label] + [0.0])
        return runtime

    def _list_outputs(self):
        out = self._outputs().get()
        infile = os.path.split(self.inputs.in_file)[1]
        base = os.path.splitext(infile)[0]
        out['out_file'] = os.path.abspath(base + '_ants.csv')
        return out


class Ants2MincPointsInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True,
                   desc='CSV file with columns x,y,z,weight,structID,patientID,label,t')
    flipxy = traits.Bool(False,
                         desc='Whether to negate the output x and y values. This is usually what you want '
                              'as ANTS uses ITK, which operates in LPS coordinates (when ANTS loads a '
                              'Nifti file it converts the affine matrix to LPS, so your ANTS points file '
                              ' should be in LPS).')


class Ants2MincPointsOutputSpec(TraitedSpec):
    out_file = File(exists=True,
                    desc='`Format reference <https://en.wikibooks.org/wiki/MINC/SoftwareDevelopment/Tag_file_format_reference>`_')


class Ants2MincPoints(BaseInterface):
    """Convert an ANTS points file
    file to an MNI points file
    """
    input_spec = Ants2MincPointsInputSpec
    output_spec = Ants2MincPointsOutputSpec

    def _run_interface(self, runtime):
        out = self._list_outputs()['out_file']
        with open(self.inputs.in_file, 'r') as f, open(out, 'w') as fout:
            reader = csv.reader(f, delimiter=',')
            fout.write('MNI Tag Point File\nVolumes = 1;\nPoints =')
            fieldnames = next(reader)
            if fieldnames != ['x', 'y', 'z', 'weight', 'structID', 'patientID', 'label', 't']:
                raise RuntimeError("Incorrect points file format")
            for row in reader:
                if self.inputs.flipxy:
                    row[0] = str(float(row[0]) * -1.0)
                    row[1] = str(float(row[1]) * -1.0)
                fout.write('\n ' + ' '.join(str(tmp) for tmp in row[:-2]) + ' "' + row[-2] + '"')
            fout.write(';\n')
        return runtime

    def _list_outputs(self):
        out = self._outputs().get()
        infile = os.path.split(self.inputs.in_file)[1]
        base = os.path.splitext(infile)[0]
        out['out_file'] = os.path.abspath(base + '_minc.tag')
        return out
