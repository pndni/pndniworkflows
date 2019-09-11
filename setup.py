from setuptools import setup, find_packages


# https://stackoverflow.com/questions/18026980/python-setuptools-how-can-i-list-a-private-repository-under-install-requires
setup(
    name='pndniworkflows',
    version='dev',
    install_requires=[
        'nipype @ git+https://github.com/stilley2/nipype.git@ac54739effc8fdd7d89a57b5aac91b3f7cefd760',
        'matplotlib>=3',
        'Jinja2>=2.10.1',
        'nibabel>=2.4.0',
        'pybids>=0.9.2',
        ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    extra_require={
        'doc': ['Sphinx', 'sphinx-argparse', 'sphinx-rtd-theme']
    },
    packages=find_packages(),
    package_data={
        '': ['templates/*tpl'],
        '': ['config/pndni_bids.json']
    },
)
