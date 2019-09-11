from nipype.interfaces.base import (File,
                                    Directory,
                                    TraitedSpec,
                                    traits,
                                    isdefined,
                                    BaseInterface,
                                    BaseInterfaceInputSpec,
                                    InputMultiPath)
import os
from pathlib import Path
from .. import viz


class ReportletCompareInputSpec(BaseInterfaceInputSpec):
    name1 = traits.Str(mandatory=True, desc='Name of first image')
    name2 = traits.Str(mandatory=True, desc='Name of second image')
    image1 = traits.Either(File(exists=True, mandatory=True, desc='First image file'), None)
    image2 = traits.Either(File(exists=True, mandatory=True, desc='Second image file'), None)
    nslices = traits.Int(7, usedefault=True, desc='Number of slices to plot')
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')
    relative_dir = Directory(exists=True, desc='Create links to filenames relative to this directory')


class ReportletCompareOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletCompare(BaseInterface):
    input_spec = ReportletCompareInputSpec
    output_spec = ReportletCompareOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.relative_dir):
            relative_dir = self.inputs.relative_dir
        else:
            relative_dir = None
        viz.compare(self.inputs.name1,
                    self.inputs.image1,
                    self.inputs.name2,
                    self.inputs.image2,
                    self._gen_outfilename(),
                    nslices=self.inputs.nslices,
                    form=self.inputs.qcform,
                    relative_dir=relative_dir)
        return runtime

    def _gen_outfilename(self):
        p = Path('compare_{}_{}.txt'.format(self.inputs.name1, self.inputs.name2)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class ReportletContourInputSpec(BaseInterfaceInputSpec):
    name = traits.Str(mandatory=True, desc='Name of image')
    image = traits.Either(File(exists=True, mandatory=True, desc='Image file'), None)
    labelimage = traits.Either(File(exists=True, mandatory=True, desc='Label image to calculate contours'), None)
    nslices = traits.Int(7, usedefault=True, desc='Number of slices to plot')
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')
    relative_dir = Directory(exists=True, desc='Create links to filenames relative to this directory')


class ReportletContourOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletContour(BaseInterface):
    input_spec = ReportletContourInputSpec
    output_spec = ReportletContourOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.relative_dir):
            relative_dir = self.inputs.relative_dir
        else:
            relative_dir = None
        viz.contours(self.inputs.name,
                     self.inputs.image,
                     self.inputs.labelimage,
                     self._gen_outfilename(),
                     nslices=self.inputs.nslices,
                     form=self.inputs.qcform,
                     relative_dir=relative_dir)
        return runtime

    def _gen_outfilename(self):
        p = Path('contour_{}.txt'.format(self.inputs.name)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class ReportletSingleInputSpec(BaseInterfaceInputSpec):
    name = traits.Str(mandatory=True, desc='Name of image')
    image = traits.Either(File(exists=True, mandatory=True, desc='Image file'), None)
    nslices = traits.Int(7, usedefault=True, desc='Number of slices to plot')
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')
    relative_dir = Directory(exists=True, desc='Create links to filenames relative to this directory')


class ReportletSingleOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletSingle(BaseInterface):
    input_spec = ReportletSingleInputSpec
    output_spec = ReportletSingleOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.relative_dir):
            relative_dir = self.inputs.relative_dir
        else:
            relative_dir = None
        viz.single(self.inputs.name,
                   self.inputs.image,
                   self._gen_outfilename(),
                   nslices=self.inputs.nslices,
                   form=self.inputs.qcform,
                   relative_dir=relative_dir)
        return runtime

    def _gen_outfilename(self):
        p = Path('single_{}.txt'.format(self.inputs.name)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class ReportletDistributionsInputSpec(BaseInterfaceInputSpec):
    name = traits.Str(mandatory=True, desc='Name of distributions')
    distsfile = traits.Either(
                    File(exists=True, mandatory=True,
                         desc='File containing distributions. '
                              'Must be a comma-separated file with two columns and no heading. '
                              'The first column is a point in distribution, and the second '
                              'is an integer indicating which distribution it belongs to.'),
                    None)
    labelfile = traits.Either(
                    File(exists=True,
                         desc='TSV file with "index" and "name" columns. Used to label distributions '
                              '("index" corresponds to the second column in distsfile)'),
                    None)
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')
    relative_dir = Directory(exists=True, desc='Create links to filenames relative to this directory')


class ReportletDistributionsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletDistributions(BaseInterface):
    input_spec = ReportletDistributionsInputSpec
    output_spec = ReportletDistributionsOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.relative_dir):
            relative_dir = self.inputs.relative_dir
        else:
            relative_dir = None
        viz.distributions(self.inputs.name,
                          self.inputs.distsfile,
                          self._gen_outfilename(),
                          self.inputs.labelfile,
                          form=self.inputs.qcform,
                          relative_dir=relative_dir)
        return runtime

    def _gen_outfilename(self):
        p = Path('dists_{}.txt'.format(self.inputs.name)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class ReportletCrashInputSpec(BaseInterfaceInputSpec):
    name = traits.Str(mandatory=True, desc='Name of distributions')
    crashfiles = traits.List(File(exists=True, mandatory=True),
                             desc='List of nipype crash files (can be empty)')
    relative_dir = Directory(exists=True, desc='Create links to filenames relative to this directory')


class ReportletCrashOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletCrash(BaseInterface):
    input_spec = ReportletCrashInputSpec
    output_spec = ReportletCrashOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.relative_dir):
            relative_dir = self.inputs.relative_dir
        else:
            relative_dir = None
        viz.crash(self.inputs.name,
                  self.inputs.crashfiles,
                  self._gen_outfilename(),
                  relative_dir=relative_dir)
        return runtime

    def _gen_outfilename(self):
        p = Path('crash_{}.txt'.format(self.inputs.name)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class AssembleReportInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True)
    title = traits.Str(mandatory=True, desc='Title of final report')
    out_file = File(desc='Output file')


class AssembleReportOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class AssembleReport(BaseInterface):
    input_spec = AssembleReportInputSpec
    output_spec = AssembleReportOutputSpec

    def _run_interface(self, runtime):
        viz.assemble(self._gen_outfilename(), self.inputs.in_files, self.inputs.title)
        return runtime

    def _gen_outfilename(self):
        if isdefined(self.inputs.out_file):
            p = Path(self.inputs.out_file).resolve()
        else:
            p = Path('report.html').resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class IndexReportInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True)
    out_file = File(mandatory=True)


class IndexReportOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class IndexReport(BaseInterface):
    input_spec = IndexReportInputSpec
    output_spec = IndexReportOutputSpec

    def _run_interface(self, runtime):
        # https://stackoverflow.com/questions/38083555/using-pathlibs-relative-to-for-directories-on-the-same-level
        out_dir = Path(self.inputs.out_file).parent
        in_files = [str(os.path.relpath(in_file, out_dir)) for in_file in self.inputs.in_files]
        viz.index(self.inputs.out_file, in_files)
        return runtime

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self.inputs.out_file
        return outputs
