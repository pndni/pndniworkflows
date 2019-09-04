"""Interfaces to the `minc toolkit <https://github.com/BIC-MNI/minc-toolkit-v2>`_

Note that many of these interfaces do not expose all command line options.

Some argument descriptions are copied from the minc help, and as such is
Copyright the MINC developers, McConnell Brain Imaging Centre,
Montreal Neurological Institute, McGill University.
"""
from nipype.interfaces.base import (CommandLine,
                                    CommandLineInputSpec,
                                    File,
                                    Directory,
                                    TraitedSpec,
                                    Undefined,
                                    traits)
from pathlib import Path


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
    """Interface to mnc2nii"""

    input_spec = Mnc2niiInputSpec
    output_spec = Mnc2niiOutputSpec
    _cmd = 'mnc2nii'


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
    """Interface to nii2mnc"""

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
    """Interface to nu_correct"""

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
    """Interface to inormalize"""

    input_spec = INormalizeInputSpec
    output_spec = INormalizeOutputSpec
    _cmd = 'inormalize'


class ClassifyInputSpec(CommandLineInputSpec):
    tag_file = File(exists=True, argstr='-tagfile %s', mandatory=True,
                    desc='`Format reference <https://en.wikibooks.org/wiki/MINC/SoftwareDevelopment/Tag_file_format_reference>`_')
    in_file = File(exists=True, position=-2, argstr='%s', mandatory=True)
    mask_file = File(exists=True, position=1, argstr='-mask %s')
    dump_features = traits.Bool(position=0, argstr='-dump_features', xor=('out_file',),
                                desc='Output the feature matrix instead of running the classifier')
    out_file = File(position=-1, genfile=True,
                    argstr='%s', xor=('dump_features',))


class ClassifyOutputSpec(TraitedSpec):
    out_file = File()
    features = File()


class Classify(CommandLine):
    """Interface to classify"""

    input_spec = ClassifyInputSpec
    output_spec = ClassifyOutputSpec
    _cmd = 'classify'
    _terminal_output = 'file_stdout'

    def _run_interface(self, runtime):
        # inspired by afni OutlierCount
        runtime = super(Classify, self)._run_interface(runtime)
        if self.inputs.dump_features:
            out_features = self._gen_outfeatures()
            with open(out_features, 'x') as f:
                f.write(runtime.stdout)
        return runtime

    def _gen_outfeatures(self):
        return str(Path('features.txt').resolve())

    def _gen_out_filename(self):
        inpath = Path(self.inputs.in_file)
        suffixes = ''.join(inpath.suffixes)
        return str(Path(inpath.stem[:-len(suffixes)] + '_classified' + suffixes).resolve())

    def _list_outputs(self):
        outputs = self.output_spec().get()
        if self.inputs.dump_features:
            outputs['features'] = self._gen_outfeatures()
        else:
            outputs['out_file'] = self._gen_out_filename()
        return outputs

    def _gen_filename(self, name):
        if name == 'out_file':
            if self.inputs.dump_features:
                # returning Undefined here should cause _parse_inputs to leave this off of the command line
                return Undefined
            else:
                return self._gen_out_filename()
        else:
            return None


class MincLookupInputSpec(CommandLineInputSpec):
    discrete = traits.Bool(argstr='-discrete', mandatory=True,
                           desc='Lookup table has discrete (integer) entries - range is ignored.')
    lut_string = traits.String(argstr='-lut_string %s', mandatory=True,
                               desc='String containing the lookup table, with ";" to separate lines.')
    in_file = File(exists=True, position=-2, argstr='%s',
                   mandatory=True)
    out_file = File(position=-1, name_source='in_file',
                    name_template='%s_lut',
                    keep_extension=True,
                    argstr='%s')


class MincLookupOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class MincLookup(CommandLine):
    """Interface to minclookup"""

    input_spec = MincLookupInputSpec
    output_spec = MincLookupOutputSpec
    _cmd = 'minclookup'
