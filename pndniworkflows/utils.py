from bids import BIDSLayout
import json
from nipype.pipeline import engine as pe
from nipype.interfaces.utility import IdentityInterface
from nipype.interfaces.base import BaseInterface, BaseInterfaceInputSpec, TraitedSpec, traits
import os
import nibabel
import numpy as np
from pathlib import Path
import pkg_resources


DERIVATIVE_PATTERNS = ['sub-{subject}/anat/sub-{subject}[_ses-{session}][_acq-{acquisition}][_ce-{contrast}][_rec-{reconstruction}][_space-{space}][_label-{label}][_skullstripped-{skullstripped}][_desc-{description}]_{suffix}.{extension<nii|nii\\.gz|json>}',
                       'sub-{subject}/xfm/sub-{subject}[_ses-{session}][_acq-{acquisition}][_ce-{contrast}][_rec-{reconstruction}][_desc-{description}]_from-{from_}_to-{to}_mode-{mode<image|points>}_{suffix<xfm>}.{extension}']


def get_subjects_node(bids_dir, subject_list=None):
    subjects = pe.Node(IdentityInterface(fields=['subject']), name='subjects')
    if subject_list is None:
        subject_list = BIDSLayout(bids_dir).get_subjects()
    subjects.iterables = ('subject', subject_list)
    return subjects


def write_dataset_description(bids_dir, **kwargs):
    for key in ['Name', 'BIDSVersion']:
        if key not in kwargs.keys():
            raise ValueError(f'{key} is a required key')
    with open(os.path.join(bids_dir, 'dataset_description.json'), 'w') as f:
        json.dump(kwargs, f, indent=4)


def get_bids_patterns():
    with open(pkg_resources.resource_filename('bids', 'layout/config/bids.json'), 'r') as f:
        patterns = json.load(f)['default_path_patterns']
    patterns.extend(DERIVATIVE_PATTERNS)
    return patterns
