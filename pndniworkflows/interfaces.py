from nipype.interfaces.base import (CommandLine,
                                    CommandLineInputSpec,
                                    Directory,
                                    File,
                                    TraitedSpec,
                                    traits,
                                    isdefined,
                                    InputMultiPath,
                                    BaseInterface,
                                    BaseInterfaceInputSpec,
                                    OutputMultiPath)
import os
import csv
from nipype.algorithms.misc import Gunzip
import nibabel
import re
from pathlib import Path
from .utils import get_bids_patterns
from bids import BIDSLayout
import shutil


# from BEP011 (https://docs.google.com/document/d/1YG2g4UkEio4t_STIBOqYOwneLEs1emHIXbGKynx7V0Y/edit#heading=h.mqkmyp254xh6)
BIDS_LABELS = [('Background', 'BG'),
               ('Grey Matter', 'GM'),
               ('White Matter', 'WM'),
               ('Cerebrospinal Fluid', 'CSF'),
               ('Grey and White Matter', 'GWM'),
               ('Bone', 'B'),
               ('Soft Tissue', 'ST'),
               ('Non-brain', 'NB'),
               ('Lesion', 'L'),
               ('Coritcal Grey Matter', 'CGM'),
               ('Subcortical Grey Matter', 'SCGM'),
               ('Brainstem', 'BS'),
               ('Cerebellum', 'CBM')]


class MncLabel2NiiLabelInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, mandatory=True, argstr='%s', position=0)
    out_file = File(argstr='%s', position=1, name_source=['in_file'],
                    hash_files=False, name_template='%s.nii')


class MncLabel2NiiLabelOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class MncLabel2NiiLabel(CommandLine):
    input_spec = MncLabel2NiiLabelInputSpec
    output_spec = MncLabel2NiiLabelOutputSpec
    _cmd = 'mnclabel2niilabel'


class Labels2ProbMapsInputSpec(CommandLineInputSpec):
    output_template = traits.Str(default='out_{label}.nii.gz', argstr='%s', position=0)
    input_files = InputMultiPath(File(exists=True), mandatory=True, argstr='%s', position=1)
    labels = traits.ListInt(minlen=1, mandatory=True, argstr='--labels %s')
    bids_labels = traits.Bool(argstr='--bids_labels',
                              desc='Assume label numbers correspond to then standard anatomical labels in BEP011')


class Labels2ProbMapsOutputSpec(TraitedSpec):
    output_files = OutputMultiPath(File(exists=True))


class Labels2ProbMaps(CommandLine):
    input_spec = Labels2ProbMapsInputSpec
    output_spec = Labels2ProbMapsOutputSpec
    _cmd = 'labels2probmaps'

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if self.inputs.bids_labels:
            labels = [BIDS_LABELS[l][1] for l in self.inputs.labels]
        else:
            labels = self.inputs.labels
        outputs['output_files'] = [os.path.abspath(self.inputs.output_template.format(label=l))
                                   for l in labels]
        return outputs


class Mnc2niiInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True,
                   position=-2, desc='input_file')
    out_file = File(argstr='%s', position=-1, desc='output file',
                    genfile=True,
                    hash_files=False,
                    name_source=['in_file'],
                    name_template='%s.nii',
                    keep_extension=False)
    _xor_outtype = ('write_byte', 'write_short', 'write_int', 'write_float', 'write_double')
    write_byte = traits.Bool(desc='Write voxel data in 8-bit integer format',
                             argstr='-byte', xor=_xor_outtype)
    write_short = traits.Bool(desc='Write voxel data in 16-bit integer format',
                              argstr='-short', xor=_xor_outtype)
    write_int = traits.Bool(desc='Write voxel data in 32-bit integer format',
                            argstr='-int', xor=_xor_outtype)
    write_float = traits.Bool(desc='Write voxel data in 32-bit floating point format',
                              argstr='-float', xor=_xor_outtype)
    write_double = traits.Bool(desc='Write voxel data in 64-bit floating point format',
                               argstr='-double', xor=_xor_outtype)

    _xor_signed = ('write_signed', 'write_unsigned')
    write_signed = traits.Bool(desc='Write integer voxel data in signed format',
                               argstr='-signed', xor=_xor_signed)
    write_unsigned = traits.Bool(desc='Write integer voxel data in unsigned format',
                                 argstr='-unsigned', xor=_xor_signed)

    noscanrange = traits.Bool(desc='Do not scan data range',
                              argstr='-noscanrange')


class Mnc2niiOutputSpec(TraitedSpec):
    out_file = File(desc='output file', exists=True)


class Mnc2nii(CommandLine):
    input_spec = Mnc2niiInputSpec
    output_spec = Mnc2niiOutputSpec
    _cmd = 'mnc2nii'


class ItemInputSpec(BaseInterfaceInputSpec):
    in_list = traits.List(trait=traits.Any())


class ItemOutputSpec(TraitedSpec):
    out_item = traits.Any()


class Item(BaseInterface):
    input_spec = ItemInputSpec
    output_spec = ItemOutputSpec

    def _run_interface(self, runtime):
        in_list = self.inputs.in_list
        if len(in_list) != 1:
            raise ValueError('Length of list does not equal 1')
        self._out_item_tmp = in_list[0]
        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        outputs['out_item'] = self._out_item_tmp
        return outputs


class SwapLabelsInputSpec(CommandLineInputSpec):
    label_map = traits.Dict(key_trait=traits.Int(), value_trait=traits.Int(), position=0, argstr='%s')
    in_file = traits.File(exists=True, argstr='%s', position=1)
    out_file = traits.File(name_source=['in_file'],
                           name_template='%s_swaplabels',
                           keep_extension=True, hash_files=False,
                           argstr='%s', position=2)


class SwapLabelsOutputSpec(TraitedSpec):
    out_file = traits.File(exists=True)


class SwapLabels(CommandLine):
    input_spec = SwapLabelsInputSpec
    output_spec = SwapLabelsOutputSpec
    _cmd = 'swaplabels'

    def _format_arg(self, name, spec, value):
        if name == 'label_map':
            return spec.argstr % ('"' + ', '.join([f'{key}: {val}' for key, val in value.items()]) + '"')
        return super(SwapLabels, self)._format_arg(name, spec, value)


class Nii2mncInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True,
                   position=-2, desc='input_file')
    out_file = File(argstr='%s', position=-1, desc='output file',
                    name_source=['in_file'], name_template='%s.mnc',
                    keep_extension=False,
                    hash_files=False)
    _xor_outtype = ('write_byte', 'write_short', 'write_int', 'write_float', 'write_double')
    write_byte = traits.Bool(desc='Write voxel data in 8-bit integer format',
                             argstr='-byte', xor=_xor_outtype)
    write_short = traits.Bool(desc='Write voxel data in 16-bit integer format',
                              argstr='-short', xor=_xor_outtype)
    write_int = traits.Bool(desc='Write voxel data in 32-bit integer format',
                            argstr='-int', xor=_xor_outtype)
    write_float = traits.Bool(desc='Write voxel data in 32-bit floating point format',
                              argstr='-float', xor=_xor_outtype)
    write_double = traits.Bool(desc='Write voxel data in 64-bit floating point format',
                               argstr='-double', xor=_xor_outtype)

    _xor_signed = ('write_signed', 'write_unsigned')
    write_signed = traits.Bool(desc='Write integer voxel data in signed format',
                               argstr='-signed', xor=_xor_signed)
    write_unsigned = traits.Bool(desc='Write integer voxel data in unsigned format',
                                 argstr='-unsigned', xor=_xor_signed)

    noscanrange = traits.Bool(desc='Do not scan data range',
                              argstr='-noscanrange')


class Nii2mncOutputSpec(TraitedSpec):
    out_file = File(desc='output file', exists=True)


class Nii2mnc(CommandLine):
    input_spec = Nii2mncInputSpec
    output_spec = Nii2mncOutputSpec
    _cmd = 'nii2mnc'


class NUCorrectInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True,
                   position=-2, desc='input file')
    out_file = File(argstr='%s', position=-1, desc='output file',
                    name_source=['in_file'],
                    name_template='%s_nucor',
                    keep_extension=True, hash_files=False)
    tmpdir = Directory(argstr='-tmpdir %s',
                       desc='temporary working directory')
    mask = File(exists=True, argstr='-mask %s',
                desc='specify region for processing')


class NUCorrectOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class NUCorrect(CommandLine):
    input_spec = NUCorrectInputSpec
    output_spec = NUCorrectOutputSpec
    _cmd = 'nu_correct'


class INormalizeInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, argstr='%s', mandatory=True,
                   position=-2, desc='input file')
    out_file = File(argstr='%s', position=-1, desc='output file',
                    name_source=['in_file'],
                    name_template='%s_inorm',
                    keep_extension=True, hash_files=False)
    const2 = traits.List(traits.Float, minlen=2, maxlen=2,
                         argstr='-const2 %s',
                         desc='specify two constant values (for -range).')
    range = traits.Float(desc='Normalize the range of <infile> to const values or model. '
                              'Requires a float argument specifying the top- and bottom % '
                              'to exclude, e.g., "-range 5"',
                         argstr='-range %f')


class INormalizeOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class INormalize(CommandLine):
    input_spec = INormalizeInputSpec
    output_spec = INormalizeOutputSpec
    _cmd = 'inormalize'


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


class NiftiTypeInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True)


class NiftiTypeOutputSpec(TraitedSpec):
    write_byte = traits.Bool()
    write_short = traits.Bool()
    write_int = traits.Bool()
    write_float = traits.Bool()
    write_double = traits.Bool()
    write_signed = traits.Bool()
    write_unsigned = traits.Bool()


class NiftyType(BaseInterface):
    input_spec = NiftiTypeInputSpec
    output_spec = NiftiTypeOutputSpec
    typemap = {'b': 'write_byte',
               'h': 'write_short',
               'i': 'write_int',
               'f': 'write_float',
               'd': 'write_double'}

    def _run_interface(self, runtime):
        t = nibabel.load(self.inputs.in_file).get_data_dtype()
        out = self._outputs().get()
        for k in out.keys():
            out[k] = False
        if t.kind == 'u':
            out['write_unsigned'] = True
        else:
            out['write_signed'] = True
        out[self.typemap[t.char.lower()]] = True
        self._output_type_flags = out
        return runtime

    def _list_outputs(self):
        return self._output_type_flags


class Minc2AntsPointsInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True)
    flipxy = traits.Bool(False)


class Minc2AntsPointsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Minc2AntsPoints(BaseInterface):
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
    in_file = File(exists=True)
    flipxy = traits.Bool(False)


class Ants2MincPointsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Ants2MincPoints(BaseInterface):
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


class ClassifyInputSpec(CommandLineInputSpec):
    tag_file = File(exists=True, argstr='-tagfile %s', mandatory=True)
    in_file = File(exists=True, position=-2, argstr='%s', mandatory=True)
    out_file = File(position=-1, name_source='in_file',
                    name_template='%s_classified',
                    keep_extension=True,
                    argstr='%s')


class ClassifyOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class Classify(CommandLine):
    input_spec = ClassifyInputSpec
    output_spec = ClassifyOutputSpec
    _cmd = 'classify'


class MincLookupInputSpec(CommandLineInputSpec):
    discrete = traits.Bool(argstr='-discrete', mandatory=True)
    lut_string = traits.String(argstr='-lut_string %s', mandatory=True)
    in_file = File(exists=True, position=-2, argstr='%s',
                   mandatory=True)
    out_file = File(position=-1, name_source='in_file',
                    name_template='%s_lut',
                    keep_extension=True,
                    argstr='%s')


class MincLookupOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class MincLookup(CommandLine):
    input_spec = MincLookupInputSpec
    output_spec = MincLookupOutputSpec
    _cmd = 'minclookup'


class CombineLabelsInputSpec(CommandLineInputSpec):
    label_files = InputMultiPath(exists=True, position=-1, argstr='%s')
    out_file = File(position=0, argstr='%s',
                    genfile=True, hash_files=False)


class CombineLabelsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class CombineLabels(CommandLine):
    input_spec = CombineLabelsInputSpec
    output_spec = CombineLabelsOutputSpec
    _cmd = 'combinelabels'

    def _gen_filename(self, name):
        if name == 'out_file':
            outfile = self._gen_outfilename()
        else:
            outfile = None
        return outfile

    def _gen_outfilename(self):
        basefile = Path(self.inputs.label_files[0])
        outfile = Path(basefile.stem + '_combined' + ''.join(basefile.suffixes))
        outfile = outfile.resolve()
        return str(outfile)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class WriteBIDSFileInputSpec(BaseInterfaceInputSpec):
    in_file = File(exists=True, mandatory=True)
    out_dir = Directory(exists=True, mandatory=True)
    subject = traits.Str(mandatory=True)
    session = traits.Str()
    acquisition = traits.Str()
    contrast = traits.Str()
    reconstruction = traits.Str()
    space = traits.Str()
    label = traits.Str()
    skullstripped = traits.Str()
    description = traits.Str()
    from_ = traits.Str()
    to = traits.Str()
    mode = traits.Str()
    suffix = traits.Str()


class WriteBIDSFileOutputSpec(TraitedSpec):
    out_file = File(exists=False)


class WriteBIDSFile(BaseInterface):
    input_spec = WriteBIDSFileInputSpec
    output_spec = WriteBIDSFileOutputSpec

    def _run_interface(self, runtime):
        b = BIDSLayout(self.inputs.out_dir, validate=False)
        args = {'extension': ''.join(Path(self.inputs.in_file).suffixes)[1:]}
        for key, val in self.inputs.get().items():
            if key in ['in_file', 'out_dir']:
                continue
            if len(val) > 0:
                args[key] = val
        p = b.build_path(args, path_patterns=get_bids_patterns(), strict=True)
        if p is None:
            raise RuntimeError('BIDSLayout was unable to build a path with parameters ' + ', '.join([f'{key}: {val}' for key, val in args.items()]))
        outfull = (Path(self.inputs.out_dir) / p).resolve()
        if outfull.exists():
            raise RuntimeError(f'{str(outfull)} already exists')
        outfull.parent.mkdir(parents=True, exist_ok=True)
        self._makebidspath_output_tmp = str(outfull)
        shutil.copy(self.inputs.in_file, outfull)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._makebidspath_output_tmp
        return outputs
