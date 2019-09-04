from nipype.interfaces.base import CommandLineInputSpec


def _insert(list_, ind, x):
    if ind is None:
        list_.append(x)
    else:
        list_.insert(ind, x)


def _writespec(lines, ind, heading, spec):
    _insert(lines, ind, '')
    _insert(lines, ind, heading)
    _insert(lines, ind, '')
    if isinstance(spec, CommandLineInputSpec):
        ignorelist = ['args', 'environ']
    else:
        ignorelist = []
    for t in spec.visible_traits():
        if t in ignorelist:
            continue
        _insert(lines, ind, ':param {}: {}'.format(t, spec.trait(t).desc))
        _insert(lines, ind, ':type {}: {}'.format(t, spec.trait(t).info()))


def proc_docstring(app, what, name, obj, options, lines):

    if hasattr(obj, 'input_spec'):
        for i, l in enumerate(lines):
            if 'Example:' == l.strip():
                ind = i - len(lines)
                break
        else:
            ind = None
        interface = obj()
        _writespec(lines, ind, 'Inputs:', interface.input_spec())
        _writespec(lines, ind, 'Outputs:', interface.output_spec())
        _insert(lines, ind, '')


def setup(app):
    app.connect('autodoc-process-docstring', proc_docstring)
