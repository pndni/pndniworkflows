from setuptools import setup, find_packages


setup(
    name='pndniworkflows',
    version='dev',
    install_requires=[
        'matplotlib>=3',
        'nipype>=1.2',
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
)
