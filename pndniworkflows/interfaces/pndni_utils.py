"""Interfaces for `pndni_utils <https://github.com/pndni/pndni_utils>`_"""
from nipype.interfaces.base import (CommandLine,
                                    CommandLineInputSpec,
                                    BaseInterfaceInputSpec,
                                    SimpleInterface,
                                    File,
                                    TraitedSpec,
                                    traits,
                                    InputMultiPath,
                                    OutputMultiPath)
import os
from pathlib import Path
from pndni.convertpoints import Points


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
