from nipype.interfaces.base import (File,
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
    image1 = File(exists=True, mandatory=True, desc='First image file')
    image2 = File(exists=True, mandatory=True, desc='Second image file')
    nslices = traits.Int(7, usedefault=True, desc='Number of slices to plot')
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')


class ReportletCompareOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletCompare(BaseInterface):
    input_spec = ReportletCompareInputSpec
    output_spec = ReportletCompareOutputSpec

    def _run_interface(self, runtime):
        viz.compare(self.inputs.name1,
                    self.inputs.image1,
                    self.inputs.name2,
                    self.inputs.image2,
                    self._gen_outfilename(),
                    nslices=self.inputs.nslices,
                    form=self.inputs.qcform)
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
    image = File(exists=True, mandatory=True, desc='Image file')
    labelimage = File(exists=True, mandatory=True, desc='Label image to calculate contours')
    nslices = traits.Int(7, usedefault=True, desc='Number of slices to plot')
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')


class ReportletContourOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletContour(BaseInterface):
    input_spec = ReportletContourInputSpec
    output_spec = ReportletContourOutputSpec

    def _run_interface(self, runtime):
        viz.contours(self.inputs.name,
                     self.inputs.image,
                     self.inputs.labelimage,
                     self._gen_outfilename(),
                     nslices=self.inputs.nslices,
                     form=self.inputs.qcform)
        return runtime

    def _gen_outfilename(self):
        p = Path('contour_{}.txt'.format(self.inputs.name)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class ReportletDistributionsInputSpec(BaseInterfaceInputSpec):
    name = traits.Str(mandatory=True, desc='Name of distributions')
    distsfile = File(exists=True, mandatory=True,
                     desc='File containing distributions. '
                          'Must be a comma-separated file with two columns and no heading. '
                          'The first column is a point in distribution, and the second '
                          'is an integer indicating which distribution it belongs to.')
    labelmap = traits.Dict(key_trait=traits.Int(), value_trait=traits.Str(),
                           desc='Mapping of distribution labels to string labels.')
    qcform = traits.Bool(True, usedefault=True, desc='Include qc form in output')


class ReportletDistributionsOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class ReportletDistributions(BaseInterface):
    input_spec = ReportletDistributionsInputSpec
    output_spec = ReportletDistributionsOutputSpec

    def _run_interface(self, runtime):
        if isdefined(self.inputs.labelmap):
            labelmap = self.inputs.labelmap
        else:
            labelmap = None
        viz.distributions(self.inputs.name,
                          self.inputs.distsfile,
                          self._gen_outfilename(),
                          labelmap,
                          form=self.inputs.qcform)
        return runtime

    def _gen_outfilename(self):
        p = Path('dists_{}.txt'.format(self.inputs.name)).resolve()
        return str(p)

    def _list_outputs(self):
        outputs = self.output_spec().get()
        outputs['out_file'] = self._gen_outfilename()
        return outputs


class AssembleReportInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True)
    title = traits.Str(mandatory=True, desc='Title of final report')


class AssembleReportOutputSpec(TraitedSpec):
    out_file = File(exists=True)


class AssembleReport(BaseInterface):
    input_spec = AssembleReportInputSpec
    output_spec = AssembleReportOutputSpec

    def _run_interface(self, runtime):
        viz.assemble(self._gen_outfilename(), self.inputs.in_files, self.inputs.title)
        return runtime

    def _gen_outfilename(self):
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
