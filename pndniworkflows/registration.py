from nipype.interfaces.ants.registration import Registration


def ants_registration_syn_node(**kwargs):
    """return antsRegistration interace instance with default values
    based on antsRegistrationSyN.sh with the s transformation option

    :param \*\*kwargs: parameters to override the default values
    :return: :py:obj:`Registration` node
    """
    defaults = dict(dimension=3,
                    use_histogram_matching=False,
                    interpolation='Linear',
                    metric=['MI', 'MI', 'CC'],
                    metric_weight=[1.0, 1.0, 1.0],
                    radius_or_number_of_bins=[32, 32, 4],
                    sampling_strategy=['Regular', 'Regular', None],
                    sampling_percentage=[0.25, 0.25, None],
                    transforms=['Rigid', 'Affine', 'SyN'],
                    transform_parameters=[(0.1, ), (0.1, ), (0.1, 3, 0)],
                    smoothing_sigmas=[[3, 2, 1, 0], [3, 2, 1, 0], [3, 2, 1, 0]],
                    sigma_units=['vox', 'vox', 'vox'],
                    shrink_factors=[[8, 4, 2, 1], [8, 4, 2, 1], [8, 4, 2, 1]],
                    number_of_iterations=[[1000, 500, 250, 100],
                                          [1000, 500, 250, 100],
                                          [100, 70, 50, 20]],
                    convergence_threshold=[1e-6, 1e-6, 1e-6],
                    convergence_window_size=[10, 10, 10],
                    winsorize_lower_quantile=0.005,
                    winsorize_upper_quantile=0.995,
                    write_composite_transform=True,
                    output_warped_image=True)
    defaults.update(kwargs)
    ants = Registration(**defaults)
    return ants


def ants_registration_affine_node(**kwargs):
    """return antsRegistration interace instance with default values
    based on antsRegistrationSyN.sh with the a transformation option

    :param \*\*kwargs: parameters to override the default values
    :return: :py:obj:`Registration` node
    """
    defaults = dict(dimension=3,
                    use_histogram_matching=False,
                    interpolation='Linear',
                    initial_moving_transform_com=1,
                    metric=['MI', 'MI'],
                    metric_weight=[1.0, 1.0],
                    radius_or_number_of_bins=[32, 32],
                    sampling_strategy=['Regular', 'Regular'],
                    sampling_percentage=[0.25, 0.25],
                    transforms=['Rigid', 'Affine'],
                    transform_parameters=[(0.1, ), (0.1, )],
                    smoothing_sigmas=[[3, 2, 1, 0], [3, 2, 1, 0]],
                    sigma_units=['vox', 'vox'],
                    shrink_factors=[[8, 4, 2, 1], [8, 4, 2, 1]],
                    number_of_iterations=[[1000, 500, 250, 100],
                                          [1000, 500, 250, 100]],
                    convergence_threshold=[1e-6, 1e-6],
                    convergence_window_size=[10, 10],
                    winsorize_lower_quantile=0.005,
                    winsorize_upper_quantile=0.995,
                    write_composite_transform=True,
                    output_warped_image=True)
    defaults.update(kwargs)
    ants = Registration(**defaults)
    return ants
