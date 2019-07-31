from nipype.pipeline import engine as pe
from nipype import IdentityInterface, Function
from .registration import ants_registration_affine_node
from nipype.interfaces.ants.resampling import ApplyTransformsToPoints


def writepoints(limits):
    from pathlib import Path
    x, y, z = limits
    with open('points.csv', 'w') as f:
        f.write('x,y,z,t\n')
        f.write(f'{x},{y},{z},0\n')
        f.write(f'{x},-{y},{z},0\n')
        f.write(f'-{x},-{y},{z},0\n')
        f.write(f'-{x},{y},{z},0\n')
    return str(Path('points.csv').resolve())


def cutimage(T1, points):
    import numpy as np
    import nibabel
    from pathlib import Path
    t1 = nibabel.load(T1)
    aff = t1.affine
    ind = np.argmax(np.abs(aff[2, :3]))
    inf_to_sup = aff[2, ind] >= 0
    with open(points, 'r') as f:
        l = f.readline()
        assert l.strip() == 'x,y,z,t'
        # flip because ants/ITK uses LPS
        points = []
        for l in f:
            x, y, z, _ = l.strip().split(',')
            points.append([-float(x), -float(y), float(z), 1.0])
        points = np.array(points)
    voxel_coords = np.linalg.solve(aff, points.T)
    if inf_to_sup:
        start = int(np.floor(np.min(voxel_coords[ind])))
        stop = t1.shape[ind]
    else:
        start = 0
        stop = int(np.ceil(np.max(voxel_coords[ind])))
    slice_ = [slice(None), slice(None), slice(None)]
    slice_[ind] = slice(start, stop)
    out = t1.slicer[tuple(slice_)]
    inpath = Path(T1)
    ext = ''.join(inpath.suffixes)
    stem = inpath.name[:-len(ext)]
    outname = str(Path(stem + '_cropped' + ext).resolve())
    out.to_filename(outname)
    return outname

    
def neck_removal_wf():
    wf = pe.Workflow('neck_removal')
    inputspec = pe.Node(IdentityInterface(['T1', 'model', 'limits']), name='inputspec')
    reg = pe.Node(ants_registration_affine_node(write_composite_transform=False), name='reg')
    wpoints = pe.Node(Function(input_names=['limits'], output_names=['points'], function=writepoints), name='wpoints')
    trpoints = pe.Node(ApplyTransformsToPoints(dimension=3), name='trpoints')
    cut = pe.Node(Function(input_names=['T1', 'points'], output_names=['noneck'], function=cutimage), name='cut')
    outputspec = pe.Node(IdentityInterface(['noneck']), name='outputspec')
    wf.connect([(inputspec, reg, [('T1', 'moving_image'),
                                  ('model', 'fixed_image')]),
                (inputspec, wpoints, [('limits', 'limits')]),
                (reg, trpoints, [('forward_transforms', 'transforms')]),
                (wpoints, trpoints, [('points', 'input_file')]),
                (trpoints, cut, [('output_file', 'points')]),
                (inputspec, cut, [('T1', 'T1')]),
                (cut, outputspec, [('noneck', 'noneck')])])
    return wf
