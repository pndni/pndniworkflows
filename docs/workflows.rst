Workflows
---------

.. autofunction:: pndniworkflows.preprocessing.neck_removal_wf

   .. workflow::
      :graph2use: flat
      :simple_form: no

      from pndniworkflows.preprocessing import neck_removal_wf
      wf = neck_removal_wf()

.. autofunction:: pndniworkflows.preprocessing.crop_wf

   .. workflow::
      :graph2use: flat
      :simple_form: no

      from pndniworkflows.preprocessing import crop_wf
      wf = crop_wf()

.. autofunction:: pndniworkflows.postprocessing.image_stats_wf

   .. workflow::
      :graph2use: flat
      :simple_form: no

      from pndniworkflows.postprocessing import image_stats_wf
      from collections import OrderedDict
      wf = image_stats_wf(['mean'], [OrderedDict([('index', 1), ('name', 'brain')])], 'mean_wf')
