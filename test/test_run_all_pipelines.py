"""
    This file contains a set of functional tests designed to check the correct execution of the pipeline and the
    different functions available in Clinica
"""

__author__ = "Arnaud Marcoux"
__copyright__ = "Copyright 2016-2018 The Aramis Lab Team"
__credits__ = ["Arnaud Marcoux"]
__license__ = "See LICENSE.txt file"
__version__ = "0.2.0"
__maintainer__ = "Arnaud Marcoux"
__email__ = "arnaud.marcoux@inria.fr"
__status__ = "Development"


import warnings
import sys

# Determine location for working_directory
warnings.filterwarnings("ignore")

if sys.platform == 'darwin':
    working_dir = '/Users/arnaud.marcoux/CI/working_dir_FU_python3'
elif sys.platform.startswith('linux'):
    working_dir = '/localdrive10TB/data/working_directory_ci_linux'
else:
    raise SystemError('Could not determine which CI machine is running : sys.platform must return darwin or linux2')


def test_run_T1FreeSurferCrossSectional():
    from clinica.pipelines.t1_freesurfer_cross_sectional.t1_freesurfer_cross_sectional_pipeline import T1FreeSurferCrossSectional
    from os.path import dirname, join, abspath

    root = join(dirname(abspath(__file__)), 'data', 'T1FreeSurferCrossSectional')

    clean_folder(join(root, 'out', 'caps'))
    clean_folder(join(working_dir, 'T1FreeSurferCrossSectional'))

    pipeline = T1FreeSurferCrossSectional(bids_directory=join(root, 'in', 'bids'),
                                          caps_directory=join(root, 'out', 'caps'),
                                          tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.parameters['recon_all_args'] = '-qcache'
    pipeline.base_dir = join(working_dir, 'T1FreeSurferCrossSectional')
    pipeline.build()
    pipeline.run()
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_T1VolumeTissueSegmentation():
    import os
    from clinica.pipelines.t1_volume_tissue_segmentation.t1_volume_tissue_segmentation_pipeline import T1VolumeTissueSegmentation
    from os.path import dirname, join, abspath
    from .comparison_functions import likeliness_measure

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeTissueSegmentation')
    clean_folder(join(working_dir, 'T1VolumeTissueSegmentation'))
    clean_folder(join(root, 'out', 'caps'))

    pipeline = T1VolumeTissueSegmentation(bids_directory=join(root, 'in', 'bids'),
                                          caps_directory=join(root, 'out', 'caps'),
                                          tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.base_dir = join(working_dir, 'T1VolumeTissueSegmentation')
    pipeline.build()
    pipeline.run()

    out_file = join(root, 'out/caps/subjects/sub-ADNI011S4105/ses-M00/t1/spm/segmentation/dartel_input/'
                    + 'sub-ADNI011S4105_ses-M00_T1w_segm-graymatter_dartelinput.nii.gz')
    if not os.path.exists(out_file):
        raise IOError('Pipeline did not produce file : ' + out_file +'. Consider rerunning test_run_T1VolumeTissueSegmentation')

    ref_file = join(root, 'ref/caps/subjects/sub-ADNI011S4105/ses-M00/t1/spm/segmentation/dartel_input/'
                    + 'sub-ADNI011S4105_ses-M00_T1w_segm-graymatter_dartelinput.nii.gz')

    assert likeliness_measure(out_file, ref_file, (1e-4, 0.05), (1e-2, 0.01))
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_T1VolumeCreateDartel():
    from clinica.pipelines.t1_volume_create_dartel.t1_volume_create_dartel_pipeline import T1VolumeCreateDartel
    from os.path import dirname, join, abspath, exists
    import shutil
    from .comparison_functions import likeliness_measure

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeCreateDartel')

    # Remove potential residual of previous UT
    clean_folder(join(working_dir, 'T1VolumeCreateDartel'))
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    # Instantiate pipeline
    pipeline = T1VolumeCreateDartel(bids_directory=join(root, 'in', 'bids'),
                                    caps_directory=join(root, 'out', 'caps'),
                                    tsv_file=join(root, 'in', 'subjects.tsv'),
                                    group_id='UnitTest')
    pipeline.base_dir = join(working_dir, 'T1VolumeCreateDartel')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Check output vs ref
    out_data_template = join(root, 'out/caps/groups/group-UnitTest/t1/group-UnitTest_template.nii.gz')
    ref_data_template = join(root, 'ref/group-UnitTest_template.nii.gz')
    assert likeliness_measure(out_data_template, ref_data_template, (1e-3, 0.1), (1e-2, 0.1))

    subjects = ['sub-ADNI011S4105', 'sub-ADNI023S4020', 'sub-ADNI035S4082', 'sub-ADNI128S4832']
    out_data_forward_def = [join(root, 'out', 'caps', 'subjects', sub, 'ses-M00', 't1', 'spm', 'dartel',
                                 'group-UnitTest', sub +
                                 '_ses-M00_T1w_target-UnitTest_transformation-forward_deformation.nii.gz')
                            for sub in subjects]
    ref_data_forward_def = [join(root, 'ref', sub
                                 + '_ses-M00_T1w_target-UnitTest_transformation-forward_deformation.nii.gz')
                            for sub in subjects]

    for i in range(len(out_data_forward_def)):
        assert likeliness_measure(out_data_forward_def[i], ref_data_forward_def[i], (1e-3, 0.25), (1e-2, 0.1))

    # Remove data in out folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_T1VolumeDartel2MNI():
    from clinica.pipelines.t1_volume_dartel2mni.t1_volume_dartel2mni_pipeline import T1VolumeDartel2MNI
    from os.path import dirname, join, abspath, exists
    import shutil
    import numpy as np
    import nibabel as nib

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeDartel2MNI')

    # Remove potential residual of previous UT
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'T1VolumeDartel2MNI'))

    # Copy necessary data from in to out
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    # Instantiate pipeline and run()
    pipeline = T1VolumeDartel2MNI(bids_directory=join(root, 'in', 'bids'),
                                  caps_directory=join(root, 'out', 'caps'),
                                  tsv_file=join(root, 'in', 'subjects.tsv'),
                                  group_id='UnitTest')
    pipeline.base_dir = join(working_dir, 'T1VolumeDartel2MNI')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Check output vs ref
    subjects = ['sub-ADNI011S4105', 'sub-ADNI023S4020', 'sub-ADNI035S4082', 'sub-ADNI128S4832']
    out_data_GM_MNI = [nib.load(join(root, 'out', 'caps', 'subjects', sub, 'ses-M00', 't1', 'spm', 'dartel', 'group-UnitTest',
                                     sub + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')).get_data()
                       for sub in subjects]
    ref_data_GM_MNI = [nib.load(join(root, 'ref', sub + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')).get_data()
                       for sub in subjects]
    for i in range(len(out_data_GM_MNI)):
        assert np.allclose(out_data_GM_MNI[i], ref_data_GM_MNI[i], rtol=1e-8, equal_nan=True)

    # Remove data in out folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_T1VolumeNewTemplate():
    from clinica.pipelines.t1_volume_new_template.t1_volume_new_template_pipeline import T1VolumeNewTemplate
    from os.path import dirname, join, abspath, exists, basename
    import numpy as np
    import nibabel as nib

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeNewTemplate')

    # Remove residual files from out folder
    clean_folder(join(root, 'out', 'caps'), recreate=True)
    clean_folder(join(working_dir, 'T1VolumeNewTemplate'))

    pipeline = T1VolumeNewTemplate(bids_directory=join(root, 'in', 'bids'),
                                   caps_directory=join(root, 'out', 'caps'),
                                   tsv_file=join(root, 'in', 'subjects.tsv'),
                                   group_id='UnitTest')
    pipeline.base_dir = join(working_dir, 'T1VolumeNewTemplate')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Check generated vs ref
    subjects = ['sub-ADNI011S4105', 'sub-ADNI023S4020', 'sub-ADNI035S4082', 'sub-ADNI128S4832']
    out_data_GM_MNI = [nib.load(join(root, 'out', 'caps', 'subjects', sub, 'ses-M00', 't1', 'spm', 'dartel', 'group-UnitTest',
                                     sub + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')).get_data()
                       for sub in subjects]
    ref_data_GM_MNI = [nib.load(join(root, 'ref', sub + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')).get_data()
                       for sub in subjects]

    # Check output vs ref
    out_data_template = nib.load(join(root, 'out/caps/groups/group-UnitTest/t1/group-UnitTest_template.nii.gz')).get_data()
    ref_data_template = nib.load(join(root, 'ref/group-UnitTest_template.nii.gz')).get_data()
    assert np.allclose(out_data_template, ref_data_template, rtol=1e-8, equal_nan=True)

    for i in range(len(out_data_GM_MNI)):
        print('Checking file ' + subjects[i] + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')
        assert np.allclose(out_data_GM_MNI[i], ref_data_GM_MNI[i], rtol=1e-4, equal_nan=True)

    # Remove data in out folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_T1VolumeExistingDartel():
    from clinica.pipelines.t1_volume_existing_dartel.t1_volume_existing_dartel_pipeline import T1VolumeExistingDartel
    from os.path import dirname, join, abspath
    import shutil
    from .comparison_functions import likeliness_measure

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeExistingDartel')
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'T1VolumeExistingDartel'))

    # Copy necessary data to run pipeline
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    # Instantiate and run pipeline
    pipeline = T1VolumeExistingDartel(bids_directory=join(root, 'in', 'bids'),
                                      caps_directory=join(root, 'out', 'caps'),
                                      tsv_file=join(root, 'in', 'subjects.tsv'),
                                      group_id='UnitTest')
    pipeline.base_dir = join(working_dir, 'T1VolumeExistingDartel')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Check output vs ref
    subjects = ['sub-ADNI011S4105', 'sub-ADNI023S4020', 'sub-ADNI035S4082', 'sub-ADNI128S4832']
    out_data_forward_def = [join(root, 'out', 'caps', 'subjects', sub, 'ses-M00', 't1', 'spm', 'dartel',
                                 'group-UnitTest',
                                 sub + '_ses-M00_T1w_target-UnitTest_transformation-forward_deformation.nii.gz')
                            for sub in subjects]
    ref_data_forward_def = [join(root, 'ref',
                                 sub + '_ses-M00_T1w_target-UnitTest_transformation-forward_deformation.nii.gz')
                            for sub in subjects]

    for i in range(len(out_data_forward_def)):
        assert likeliness_measure(out_data_forward_def[i], ref_data_forward_def[i], (1e-3, 0.25), (1e-2, 0.1))

    # Remove data in out folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_T1VolumeExistingTemplate():
    from clinica.pipelines.t1_volume_existing_template.t1_volume_existing_template_pipeline import T1VolumeExistingTemplate
    from os.path import dirname, join, abspath
    import shutil
    from .comparison_functions import likeliness_measure

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeExistingTemplate')

    # Remove residual files from out folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))
    clean_folder(join(working_dir, 'T1VolumeExistingTemplate'))

    pipeline = T1VolumeExistingTemplate(bids_directory=join(root, 'in', 'bids'),
                                        caps_directory=join(root, 'out', 'caps'),
                                        tsv_file=join(root, 'in', 'subjects.tsv'),
                                        group_id='UnitTest')
    pipeline.base_dir = join(working_dir, 'T1VolumeExistingTemplate')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Check generated vs ref
    subjects = ['sub-ADNI011S4105', 'sub-ADNI023S4020']
    out_data_GM_MNI = [join(root, 'out', 'caps', 'subjects', sub, 'ses-M00', 't1', 'spm', 'dartel', 'group-UnitTest',
                            sub + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')
                       for sub in subjects]
    ref_data_GM_MNI = [join(root, 'ref', sub + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')
                       for sub in subjects]

    for i in range(len(out_data_GM_MNI)):
        print('Checking file ' + subjects[i]
              + '_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_fwhm-8mm_probability.nii.gz')
        assert likeliness_measure(out_data_GM_MNI[i], ref_data_GM_MNI[i], (1e-2, 0.04), (1e-1, 0.01))

    # Remove data in out folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_T1VolumeParcellation():
    from clinica.pipelines.t1_volume_parcellation.t1_volume_parcellation_pipeline import T1VolumeParcellation
    from os.path import dirname, join, abspath, exists
    import shutil
    import pandas as pds
    import numpy as np

    root = join(dirname(abspath(__file__)), 'data', 'T1VolumeParcellation')
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'T1VolumeParcellation'))

    # Copy data for use of pipeline
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    # Instantiate pipeline
    pipeline = T1VolumeParcellation(bids_directory='./4',
                                    caps_directory=join(root, 'out', 'caps'),
                                    tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.parameters['group_id'] = 'UnitTest'
    pipeline.parameters['atlases'] = ['AAL2', 'LPBA40', 'Neuromorphometrics', 'AICHA', 'Hammers']
    pipeline.parameters['modulate'] = 'on'
    pipeline.base_dir = join(working_dir, 'T1VolumeParcellation')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    out_files = [join(root, 'out/caps/subjects/sub-ADNI018S4696/ses-M00/t1/spm/dartel/group-UnitTest/atlas_statistics',
                      'sub-ADNI018S4696_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_probability_space-'
                      + atlas + '_map-graymatter_statistics.tsv')
                 for atlas in pipeline.parameters['atlases']]
    ref_files = [join(root, 'ref/sub-ADNI018S4696_ses-M00_T1w_segm-graymatter_space-Ixi549Space_modulated-on_probability_space-'
                      + atlas + '_map-graymatter_statistics.tsv')
                 for atlas in pipeline.parameters['atlases']]

    for i in range(len(out_files)):
        out_csv = pds.read_csv(out_files[i], sep='\t')
        ref_csv = pds.read_csv(ref_files[i], sep='\t')
        assert np.allclose(np.array(out_csv.mean_scalar), np.array(ref_csv.mean_scalar), rtol=1e-8, equal_nan=True)

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_DWIPreprocessingUsingT1():
    from clinica.pipelines.dwi_preprocessing_using_t1.dwi_preprocessing_using_t1_pipeline import DWIPreprocessingUsingT1
    from os.path import dirname, join, abspath
    from .comparison_functions import similarity_measure

    root = join(dirname(abspath(__file__)), 'data', 'DWIPreprocessingUsingT1')

    # Remove old instance of UT
    clean_folder(join(root, 'out', 'caps'))
    clean_folder(join(working_dir, 'DWIPreprocessingUsingT1'))

    pipeline = DWIPreprocessingUsingT1(bids_directory=join(root, 'in', 'bids'),
                                       caps_directory=join(root, 'out', 'caps'),
                                       tsv_file=join(root, 'in', 'subjects.tsv'),
                                       low_bval=5)
    pipeline.parameters['epi_param'] = dict([('readout_time', 0.0348756),  ('enc_dir', 'y')])
    pipeline.base_dir = join(working_dir, 'DWIPreprocessingUsingT1')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Assert :
    out_file = join(root, 'out', 'caps', 'subjects', 'sub-CAPP01001TMM', 'ses-M00', 'dwi', 'preprocessing', 'sub-CAPP01001TMM_ses-M00_dwi_space-T1w_preproc.nii.gz')
    ref_file = join(root, 'ref', 'sub-CAPP01001TMM_ses-M00_dwi_space-T1w_preproc.nii.gz')

    assert similarity_measure(out_file, ref_file, 0.97)

    # Delete out/caps folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_DWIPreprocessingUsingPhaseDiffFieldmap():
    from clinica.pipelines.dwi_preprocessing_using_phasediff_fieldmap.dwi_preprocessing_using_phasediff_fieldmap_pipeline import DWIPreprocessingUsingPhaseDiffFieldmap
    from os.path import dirname, join, abspath
    from .comparison_functions import similarity_measure
    import warnings
    warnings.filterwarnings("ignore")


    root = join(dirname(abspath(__file__)), 'data', 'DWIPreprocessingUsingPhaseDiffFieldmap')

    # Remove old instance of UT
    clean_folder(join(root, 'out', 'caps'))
    clean_folder(join(working_dir, 'DWIPreprocessingUsingPhaseDiffFieldmap'))

    pipeline = DWIPreprocessingUsingPhaseDiffFieldmap(bids_directory=join(root, 'in', 'bids'),
                                                      caps_directory=join(root, 'out', 'caps'),
                                                      tsv_file=join(root, 'in', 'subjects.tsv'),
                                                      low_bval=5)
    pipeline.base_dir = join(working_dir, 'DWIPreprocessingUsingPhaseDiffFieldmap')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Assert :
    out_file = join(root, 'out', 'caps', 'subjects', 'sub-CAPP01001TMM', 'ses-M00', 'dwi', 'preprocessing', 'sub-CAPP01001TMM_ses-M00_dwi_space-b0_preproc.nii.gz')
    ref_file = join(root, 'ref', 'sub-CAPP01001TMM_ses-M00_dwi_space-T1w_preproc.nii.gz')

    assert similarity_measure(out_file, ref_file, 0.955)

    # Delete out/caps folder
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_DWIProcessingDTI():
    # TODO : Alex must resolve the repetability issue (out file is never the same) -  assert deactivated
    from clinica.pipelines.dwi_processing_dti.dwi_processing_dti_pipeline import DWIProcessingDTI
    from os.path import dirname, join, abspath, exists
    import shutil
    import pandas as pds
    import numpy as np

    root = join(dirname(abspath(__file__)), 'data', 'DWIProcessingDTI')

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'DWIProcessingDTI'))
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    pipeline = DWIProcessingDTI(caps_directory=join(root, 'out', 'caps'),
                                tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.base_dir = join(working_dir, 'DWIProcessingDTI')
    pipeline.build()
    pipeline.run()

    # Check files
    maps = ['AD', 'FA', 'MD', 'RD']
    out_files = [join(root, 'out/caps/subjects/sub-CAPP01001TMM/ses-M00/dwi/dti_based_processing/atlas_statistics/sub-CAPP01001TMM_ses-M00_dwi_space-JHUDTI81_res-1x1x1_map-' + m + '_statistics.tsv')
                 for m in maps]
    ref_files = [join(root, 'ref', 'sub-CAPP01001TMM_ses-M00_dwi_space-JHUDTI81_res-1x1x1_map-' + m + '_statistics.tsv')
                 for m in maps]

    for i in range(len(out_files)):
        out_csv = pds.read_csv(out_files[i], sep='\t')
        out_mean_scalar = np.array(out_csv.mean_scalar)
        ref_csv = pds.read_csv(ref_files[i], sep='\t')
        ref_mean_scalar = np.array(ref_csv.mean_scalar)
        # Uncomment when problem is solved
        assert np.allclose(out_mean_scalar, ref_mean_scalar, rtol=0.025, equal_nan=True)

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_fMRIPreprocessing():
    from clinica.pipelines.fmri_preprocessing.fmri_preprocessing_pipeline import fMRIPreprocessing
    from .comparison_functions import similarity_measure
    from os.path import dirname, join, abspath
    import shutil

    root = join(dirname(abspath(__file__)), 'data', 'fMRIPreprocessing')

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'fMRIPreprocessing'))
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    pipeline = fMRIPreprocessing(bids_directory=join(root, 'in', 'bids'),
                                 caps_directory=join(root, 'out', 'caps'),
                                 tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.parameters = {
        'full_width_at_half_maximum': [8, 8, 8],
        't1_native_space': False,
        'freesurfer_brain_mask': False,
        'unwarping': False
    }
    pipeline.base_dir = join(working_dir, 'fMRIPreprocessing')
    pipeline.build()
    pipeline.run()

    out_files = [join(root, 'out/caps/subjects/sub-20110506MEMEPPAT27/ses-M00/fmri/preprocessing/sub-20110506MEMEPPAT27_ses-M00_task-rest_bold_space-Ixi549Space_preproc.nii.gz'),
                 join(root, 'out/caps/subjects/sub-20110506MEMEPPAT27/ses-M00/fmri/preprocessing/sub-20110506MEMEPPAT27_ses-M00_task-rest_bold_space-meanBOLD_preproc.nii.gz')]

    ref_files = [join(root, 'ref', 'sub-20110506MEMEPPAT27_ses-M00_task-rest_bold_space-Ixi549Space_preproc.nii.gz'),
                 join(root, 'ref', 'sub-20110506MEMEPPAT27_ses-M00_task-rest_bold_space-meanBOLD_preproc.nii.gz')]

    for i in range(len(out_files)):
        assert similarity_measure(out_files[i], ref_files[i], 0.99)

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_PETVolume():
    from clinica.pipelines.pet_volume.pet_volume_pipeline import PETVolume
    from os.path import dirname, join, abspath, exists
    import shutil
    from .comparison_functions import likeliness_measure

    root = join(dirname(abspath(__file__)), 'data', 'PETVolume')

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'PETVolume'))
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    pipeline = PETVolume(bids_directory=join(root, 'in', 'bids'),
                         caps_directory=join(root, 'out', 'caps'),
                         tsv_file=join(root, 'in', 'subjects.tsv'),
                         group_id='UnitTest',
                         fwhm_tsv=None)
    pipeline.base_dir = join(working_dir, 'PETVolume')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    subjects = ['sub-ADNI011S4105', 'sub-ADNI023S4020', 'sub-ADNI035S4082', 'sub-ADNI128S4832']
    out_files = [join(root, 'out/caps/subjects/' + sub + '/ses-M00/pet/preprocessing/group-UnitTest',
                      sub +'_ses-M00_task-rest_acq-fdg_pet_space-Ixi549Space_suvr-pons_mask-brain_fwhm-8mm_pet.nii.gz')
                 for sub in subjects]
    ref_files = [join(root, 'ref', sub + '_ses-M00_task-rest_acq-fdg_pet_space-Ixi549Space_suvr-pons_mask-brain_fwhm-8mm_pet.nii.gz')
                 for sub in subjects]

    for i in range(len(out_files)):
        assert likeliness_measure(out_files[i], ref_files[i], (1e-2, 0.25), (1e-1, 0.001))

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_StatisticsSurface():
    from clinica.pipelines.statistics_surface.statistics_surface_pipeline import StatisticsSurface
    from os.path import dirname, join, abspath, exists
    import shutil
    import numpy as np
    from scipy.io import loadmat

    root = join(dirname(abspath(__file__)), 'data', 'StatisticsSurface')

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'StatisticsSurface'))
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    pipeline = StatisticsSurface(caps_directory=join(root, 'out', 'caps'),
                                 tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.parameters = {
            'design_matrix': '1 + group + age + sex',
            'contrast': 'group',
            'str_format': '%s %s %s %f %s',
            'group_label': 'UnitTest',
            'glm_type': 'group_comparison',
            'custom_file': '@subject/@session/t1/freesurfer_cross_sectional/@subject_@session/surf/@hemi.thickness.fwhm@fwhm.fsaverage.mgh',
            'feature_label': 'cortical_thickness',
            'full_width_at_half_maximum': 20,
            'threshold_uncorrected_pvalue': 0.001,
            'threshold_corrected_pvalue': 0.05,
            'cluster_threshold': 0.001
    }
    pipeline.base_dir = join(working_dir, 'StatisticsSurface')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 8})

    # Check files
    out_file = join(root, 'out/caps/groups/group-UnitTest/statistics/surfstat_group_comparison/group-UnitTest_AD-lt-CN_measure-cortical_thickness_fwhm-20_correctedPValue.mat')
    ref_file = join(root, 'ref/group-UnitTest_AD-lt-CN_measure-cortical_thickness_fwhm-20_correctedPValue.mat')

    out_file_mat = loadmat(out_file)['correctedpvaluesstruct']
    ref_file_mat = loadmat(ref_file)['correctedpvaluesstruct']
    for i in range(4):
        assert np.allclose(out_file_mat[0][0][i], ref_file_mat[0][0][i], rtol=1e-8, equal_nan=True)
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass

def test_run_PETSurface():
    # TODO once freesurfer6 is available, uncomment lines !
    from clinica.pipelines.pet_surface.pet_surface_pipeline import PetSurface
    from os.path import dirname, join, abspath
    import shutil
    import nibabel as nib
    import numpy as np

    root = join(dirname(abspath(__file__)), 'data', 'PETSurface')

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    clean_folder(join(working_dir, 'PETSurface'))
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))

    pipeline = PetSurface(bids_directory=join(root, 'in', 'bids'),
                          caps_directory=join(root, 'in', 'caps'),
                          tsv_file=join(root, 'in', 'subjects.tsv'))
    pipeline.parameters['pet_type'] = 'fdg'
    pipeline.parameters['wd'] = join(working_dir, 'PETSurface')
    pipeline.build()
    #pipeline.run()

    # Check files
    out_files = [join(root, 'out/caps/subjects/sub-ADNI011S4105/ses-M00/pet/surface',
                      'sub-ADNI011S4105_ses-M00_task-rest_acq-FDG_pet_space-fsaverage_suvr-pons_pvc-iy_hemi-'
                      + h + '_fwhm-' + str(f) + '_projection.mgh')
                 for h in ['lh', 'rh']
                 for f in [0, 5, 10, 15, 20, 25]]
    ref_files = [join(root, 'ref/sub-ADNI011S4105_ses-M00_task-rest_acq-FDG_pet_space-fsaverage_suvr-pons_pvc-iy_hemi-'
                      + h + '_fwhm-' + str(f) + '_projection.mgh')
                 for h in ['lh', 'rh']
                 for f in [0, 5, 10, 15, 20, 25]]

    for i in range(len(out_files)):
         assert np.allclose(np.squeeze(nib.load(out_files[i]).get_data()),
                            np.squeeze(nib.load(ref_files[i]).get_data()),
                            rtol=1e-8, equal_nan=True)
    clean_folder(join(root, 'out', 'caps'), recreate=False)
    pass


def test_run_WorkflowsML():
    # TODO check end results
    from clinica.pipelines.machine_learning.ml_workflows import RB_RepHoldOut_LogisticRegression, VertexB_RepHoldOut_dualSVM, RB_RepHoldOut_RandomForest, VB_KFold_DualSVM
    from os.path import dirname, join, abspath
    from os import makedirs
    import shutil
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)

    root = join(dirname(abspath(__file__)), 'data', 'WorkflowsML')
    root_input = join(dirname(abspath(__file__)), 'data', 'InputsML')

    caps_dir = join(root_input, 'in', 'caps')
    tsv = join(root_input, 'in', 'subjects.tsv')
    diagnoses_tsv = join(root_input, 'in', 'diagnosis.tsv')
    group_id = 'allADNIdartel'

    output_dir1 = join(root, 'out', 'VertexB_RepHoldOut_dualSVM')
    clean_folder(output_dir1, recreate=True)
    wf1 = VertexB_RepHoldOut_dualSVM(caps_dir, tsv, diagnoses_tsv, group_id, output_dir1, image_type='fdg', fwhm=20,
                                     n_threads=8, n_iterations=10, grid_search_folds=3, test_size=0.3)
    wf1.run()
    shutil.rmtree(output_dir1)

    output_dir2 = join(root, 'out', 'RB_RepHoldOut_LogisticRegression')
    clean_folder(output_dir2, recreate=True)
    wf2 = RB_RepHoldOut_LogisticRegression(caps_dir, tsv, diagnoses_tsv, group_id, 'fdg', 'AICHA', output_dir2,
                                           n_threads=8, n_iterations=10, grid_search_folds=3, test_size=0.3)
    wf2.run()
    shutil.rmtree(output_dir2)

    output_dir3 = join(root, 'out', 'RB_RepHoldOut_RandomForest')
    clean_folder(output_dir3, recreate=True)
    wf3 = RB_RepHoldOut_RandomForest(caps_dir, tsv, diagnoses_tsv, group_id, 'T1', 'AAL2', output_dir3, n_threads=8,
                                     n_iterations=10, grid_search_folds=3, test_size=0.3)
    wf3.run()
    shutil.rmtree(output_dir3)

    output_dir4 = join(root, 'out', 'VB_KFold_DualSVM')
    clean_folder(output_dir4, recreate=True)
    wf4 = VB_KFold_DualSVM(caps_dir, tsv, diagnoses_tsv, group_id, 'fdg', output_dir4, fwhm=8, n_threads=8, n_folds=5,
                           grid_search_folds=3)
    wf4.run()
    shutil.rmtree(output_dir4)
    pass


def test_run_Oasis2Bids():
    from clinica.iotools.converters.oasis_to_bids.oasis_to_bids import OasisToBids
    from os.path import dirname, join, abspath
    from os import system, remove
    from filecmp import cmp

    root = join(dirname(abspath(__file__)), 'data', 'Oasis2Bids')

    clean_folder(join(root, 'out', 'bids'), recreate=True)

    # Data location
    dataset_directory = join(root, 'in', 'unorganized')
    bids_directory = join(root, 'out', 'bids')
    clinical_data_directory = join(root, 'in', 'clinical_data')

    oasis_to_bids = OasisToBids()
    oasis_to_bids.convert_images(dataset_directory, bids_directory)
    oasis_to_bids.convert_clinical_data(clinical_data_directory, bids_directory)

    # Generate tree of output files
    bids_out_txt = join(root, 'out', 'bids_out_oasis.txt')
    bids_ref_txt = join(root, 'ref', 'bids_ref_oasis.txt')
    system('cd ' + bids_directory + ' && tree > ' + bids_out_txt)
    system('cd ' + join(root, 'ref', 'bids') + ' && tree > ' + bids_ref_txt)

    # Compare them
    if not cmp(bids_out_txt, bids_ref_txt):
        with open(bids_out_txt, 'r') as fin:
            out_message = fin.read()
        with open(bids_ref_txt, 'r') as fin:
            ref_message = fin.read()
        remove(bids_out_txt)
        remove(bids_ref_txt)
        raise ValueError('Comparison of out and ref directories shows mismatch :\n '
                         'OUT :\n' + out_message + '\n REF :\n' + ref_message)

    # Clean folders
    remove(bids_out_txt)
    remove(bids_ref_txt)
    clean_folder(join(root, 'out', 'bids'), recreate=True)
    pass


def test_run_Adni2Bids():
    from clinica.iotools.converters.adni_to_bids.adni_to_bids import AdniToBids
    from os.path import dirname, join, abspath
    from os import system, remove
    from filecmp import cmp

    root = join(dirname(abspath(__file__)), 'data', 'Adni2Bids')

    clean_folder(join(root, 'out', 'bids'), recreate=True)

    adni_to_bids = AdniToBids()
    adni_to_bids.check_adni_dependencies()

    dataset_directory = join(root, 'in', 'unorganized_data')
    clinical_data_directory = join(root, 'in', 'ADNI_clinical_data_new')
    bids_directory = join(root, 'out', 'bids')
    subjects_list = join(root, 'in', 'subjects.txt')
    # modalities = ['T1', 'PET_FDG', 'PET_AV45', 'DWI', 'fMRI']
    modalities = ['T1', 'PET_FDG', 'PET_AV45']
    adni_to_bids.convert_images(dataset_directory,
                                clinical_data_directory,
                                bids_directory,
                                subjects_list,
                                modalities)

    # Generate tree of output files
    bids_out_txt = join(root, 'out', 'bids_out_adni.txt')
    bids_ref_txt = join(root, 'ref', 'bids_ref_adni.txt')
    system('cd ' + bids_directory + ' && tree  > ' + bids_out_txt)
    system('cd ' + join(root, 'ref', 'bids') + ' && tree  > ' + bids_ref_txt)

    # Compare them
    if not cmp(bids_out_txt, bids_ref_txt):
        with open(bids_out_txt, 'r') as fin:
            out_message = fin.read()
        with open(bids_ref_txt, 'r') as fin:
            ref_message = fin.read()
        remove(bids_out_txt)
        remove(bids_ref_txt)
        raise ValueError('Comparison of out and ref directories shows mismatch :\n '
                         'OUT :\n' + out_message + '\n REF :\n' + ref_message)

    # Clean folders
    remove(bids_out_txt)
    remove(bids_ref_txt)
    clean_folder(join(root, 'out', 'bids'), recreate=True)
    pass


def test_run_CreateSubjectSessionList():
    from os.path import join, dirname, abspath
    from os import remove
    from clinica.iotools.utils import data_handling as dt
    from .comparison_functions import identical_subject_list

    root = join(dirname(abspath(__file__)), 'data', 'CreateSubjectSessionList')

    # Set variables
    bids_directory = join(root, 'in', 'bids')
    output_directory = join(root, 'out')
    tsv_name = 'subject_session_list.tsv'

    # Create subject_session file
    dt.create_subs_sess_list(bids_directory, output_directory, tsv_name)

    # Comparison bitwise
    out_tsv = join(output_directory, tsv_name)
    ref_tsv = join(root, 'ref', tsv_name)
    assert identical_subject_list(out_tsv, ref_tsv)
    remove(out_tsv)
    pass


def test_run_CreateMergeFile():
    from os.path import join, dirname, abspath
    from os import remove
    from filecmp import cmp
    import shutil
    from clinica.iotools.utils import data_handling as dt

    root = join(dirname(abspath(__file__)), 'data', 'CreateMergeFile')

    bids_directory = join(root, 'in', 'bids')
    out_tsv = join(root, 'out', 'output_file.tsv')
    subject_session_tsv = join(root, 'in', 'subjects_sessions.tsv')

    clean_folder(join(root, 'out', 'caps'), recreate=False)
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))
    caps_directory = join(root, 'out', 'caps')

    dt.create_merge_file(bids_directory,
                         out_tsv,
                         caps_dir=caps_directory,
                         pipelines=None,
                         atlas_selection=None,
                         pvc_restriction=None,
                         tsv_file=subject_session_tsv,
                         group_selection=None)
    # Comparison step
    ref_tsv = join(root, 'ref', 'output_file.tsv')
    assert cmp(out_tsv, ref_tsv)
    remove(out_tsv)
    pass


def test_run_ComputeMissingModalities():
    from os.path import join, dirname, abspath, exists
    from os import remove
    from clinica.iotools.utils import data_handling as dt
    from .comparison_functions import same_missing_modality_tsv

    root = join(dirname(abspath(__file__)), 'data', 'ComputeMissingMod')

    bids_directory = join(root, 'in', 'bids')
    output_directory = join(root, 'out')
    output_name = 'missing_modalities'

    dt.compute_missing_mods(bids_directory, output_directory, output_name)

    filenames = ['missing_modalities_ses-M00.tsv',
                 'missing_modalities_ses-M03.tsv',
                 'missing_modalities_ses-M06.tsv',
                 'missing_modalities_ses-M12.tsv',
                 'missing_modalities_ses-M24.tsv',
                 'missing_modalities_ses-M48.tsv']
    for i in range(len(filenames)):
        outname = join(root, 'out', filenames[i])
        refname = join(root, 'ref', filenames[i])
        if not exists(outname):
            raise FileNotFoundError('A file called ' + outname + ' should have been generated, but it does not exists')
        assert same_missing_modality_tsv(outname, refname)
        remove(join(root, 'out', filenames[i]))
    pass


def test_run_Aibl2Bids():
    from clinica.iotools.converters.aibl_to_bids.aibl_to_bids import convert_clinical_data, convert_images
    from os.path import dirname, join, abspath

    root = join(dirname(abspath(__file__)), 'data', 'Aibl2Bids')

    dataset_directory = join(root, 'in', 'unorganized_data')
    clinical_data_directory = join(root, 'in', 'Data_extract_3.2.5')
    bids_directory = join(root, 'out', 'bids')

    clean_folder(join(root, 'out', 'bids'), recreate=True)

    convert_images(dataset_directory, clinical_data_directory, bids_directory)
    convert_clinical_data(bids_directory, clinical_data_directory)
    pass

def test_run_SVMRegularization():
    from clinica.pipelines.svm_regularization.svm_regularization_pipeline import SVMRegularization
    from os.path import dirname, join, abspath, exists
    import shutil
    import numpy as np
    import nibabel as nib
    root = join(dirname(abspath(__file__)), 'data', 'SVMReg')

    # Remove potential residual of previous UT
    clean_folder(join(root, 'out', 'caps'), recreate=False)

    #Copy necessary data from in to out
    shutil.copytree(join(root, 'in', 'caps'), join(root, 'out', 'caps'))
    # Instantiate pipeline and run()
    pipeline = SVMRegularization(caps_directory=join(root, 'out', 'caps'),
                                 tsv_file=join(root, 'in', 'subjects.tsv'))

    pipeline.parameters['group_id'] = 'ADCNbaseline'
    pipeline.parameters['fwhm'] = 4
    pipeline.parameters['h'] = 1.5
    pipeline.parameters['image_type'] = 't1'
    pipeline.parameters['pet_type'] = 'fdg'
    pipeline.base_dir = join(working_dir, 'SVMRegularization')
    pipeline.build()
    pipeline.run(plugin='MultiProc', plugin_args={'n_procs': 4})

    # Check output vs ref
    subjects = ['sub-ADNI002S4213', 'sub-ADNI011S4075']
    out_data_REG_NIFTI = [nib.load(join(root, 'out', 'caps', 'subjects', sub, 'ses-M00', 't1', 'input_regularised_svm', 'group-ADCNbaseline',
                                        sub + '_ses-M00_segm-graymatter_space-Ixi549Space_modulated-on_regularization-Fisher_fwhm-4_probability.nii.gz')).get_data()
                          for sub in subjects]
    ref_data_REG_NIFTI = [nib.load(join(root, 'ref', sub + '_ses-M00_segm-graymatter_space-Ixi549Space_modulated-on_regularization-Fisher_fwhm-4.0_probability.nii.gz')).get_data()
                          for sub in subjects]
    for i in range(len(out_data_REG_NIFTI)):
        assert np.allclose(out_data_REG_NIFTI[i], ref_data_REG_NIFTI[i], rtol=1e-3, equal_nan=True)

    # Remove data in out folder
    clean_folder(join(root, 'out', 'caps'), recreate=True)
    pass

def clean_folder(path, recreate=True):
    from os.path import abspath, exists
    from shutil import rmtree
    from os import makedirs

    abs_path = abspath(path)
    if exists(abs_path):
        rmtree(abs_path)
        if recreate:
            makedirs(abs_path)
    pass