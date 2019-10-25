"""Interfaces for `pndni_utils <https://github.com/pndni/pndni_utils>`_"""
from nipype.interfaces.base import (CommandLine,
                                    CommandLineInputSpec,
                                    File,
                                    TraitedSpec,
                                    traits,
                                    InputMultiPath,
                                    OutputMultiPath)
import os
from pathlib import Path


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
    output_template = traits.Str(default='out_{label}.nii.gz', argstr='%s', position=0,
                                 desc='Template string for output files. Must contain {label}.')
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


class SwapLabelsInputSpec(CommandLineInputSpec):
    label_map = traits.Dict(key_trait=traits.Int(), value_trait=traits.Int(), position=0, argstr='%s')
    in_file = File(exists=True, argstr='%s', position=1)
    out_file = File(name_source=['in_file'],
                    name_template='%s_swaplabels',
                    keep_extension=True, hash_files=False,
                    argstr='%s', position=2)


class SwapLabelsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class SwapLabels(CommandLine):
    input_spec = SwapLabelsInputSpec
    output_spec = SwapLabelsOutputSpec
    _cmd = 'swaplabels'

    def _format_arg(self, name, spec, value):
        if name == 'label_map':
            return spec.argstr % ('"' + ', '.join([f'{key}: {val}' for key, val in value.items()]) + '"')
        return super(SwapLabels, self)._format_arg(name, spec, value)


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


class ForceQFormInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, desc='Input NIFTI file', mandatory=True,
                   argstr='%s', position=0)
    out_file = File(argstr='%s', position=1, name_source=['in_file'],
                    hash_files=False, name_template='%s_qform',
                    keep_extension=True)
    maxangle = traits.Float(argstr='--maxangle %s', position=2)


class ForceQFormOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output file')


class ForceQForm(CommandLine):
    input_spec = ForceQFormInputSpec
    output_spec = ForceQFormOutputSpec
    _cmd = 'forceqform'


class MncDefaultDircosInputSpec(CommandLineInputSpec):
    in_file = File(exists=True, desc='Input MINC 2.0 file', mandatory=True,
                   argstr='%s', position=0)
    out_file = File(argstr='%s', position=1, name_source=['in_file'],
                    hash_files=False, name_template='%s_dircosfix',
                    keep_extension=True)


class MncDefaultDircosOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='Output file')


class MncDefaultDircos(CommandLine):
    input_spec = MncDefaultDircosInputSpec
    output_spec = MncDefaultDircosOutputSpec
    _cmd = 'minc_default_dircos'
