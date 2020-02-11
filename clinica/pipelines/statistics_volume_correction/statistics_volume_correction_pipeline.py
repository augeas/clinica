"""Statistics_Volume_Correction - Clinica Pipeline.
This file has been generated automatically by the `clinica generate template`
command line tool. See here for more details: https://gitlab.icm-institute.org/aramislab/clinica/wikis/docs/InteractingWithClinica.
"""

import clinica.pipelines.engine as cpe


class StatisticsVolumeCorrection(cpe.Pipeline):
    """Statistics_Volume_Correction


    """


    def check_custom_dependencies(self):
        """Check dependencies that can not be listed in the `info.json` file.
        """
        pass


    def get_input_fields(self):
        """Specify the list of possible inputs of this pipeline.

        Returns:
            A list of (string) input fields name.
        """

        return ['t_map']


    def get_output_fields(self):
        """Specify the list of possible outputs of this pipeline.

        Returns:
            A list of (string) output fields name.
        """

        return []


    def build_input_node(self):
        """Build and connect an input node to the pipeline.
        """

        import nipype.interfaces.utility as nutil
        import nipype.pipeline.engine as npe
        from clinica.utils.inputs import clinica_group_reader
        from clinica.utils.exceptions import ClinicaException

        all_errors = []
        try:
            t_map = clinica_group_reader(self.caps_directory, {'pattern': self.parameters['t_map'] + '*',
                                                               'description': 'statistics t map',
                                                               'needed_pipeline': 'statistics-volume'})
        except ClinicaException as e:
            all_errors.append(e)

        read_parameters_node = npe.Node(name="LoadingCLIArguments",
                                        interface=nutil.IdentityInterface(
                                            fields=self.get_input_fields(),
                                            mandatory_inputs=True))
        read_parameters_node.inputs.t_map = t_map

        self.connect([
            (read_parameters_node,      self.input_node,    [('t_map', 't_map')])
        ])


    def build_output_node(self):
        """Build and connect an output node to the pipeline.
        """

        # In the same idea as the input node, this output node is supposedly
        # used to write the output fields in a CAPS. It should be executed only
        # if this pipeline output is not already connected to a next Clinica
        # pipeline.

        pass


    def build_core_nodes(self):
        """Build and connect the core nodes of the pipeline.
        """

        import clinica.pipelines.statistics_volume_correction.statistics_volume_correction_utils as utils
        import nipype.interfaces.utility as nutil
        import nipype.pipeline.engine as npe
        from os.path import join, abspath, pardir, dirname
        import numpy as np

        peak_correction_FWE = npe.Node(name='peak_correction_FWE',
                                       interface=nutil.Function(
                                           input_names=['t_map', 't_threshold'],
                                           output_names=['output'],
                                           function=utils.peak_correction))
        peak_correction_FWE.inputs.t_threshold = self.parameters['FWEp']

        peak_correction_FDR = peak_correction_FWE.clone(name='peak_correction_FDR')
        peak_correction_FDR.inputs.t_threshold = self.parameters['FDRp']

        cluster_correction_FWE = npe.Node(name='cluster_correction_FWE',
                                          interface=nutil.Function(
                                              input_names=['t_map', 't_thresh', 'c_thresh'],
                                              output_names=['output'],
                                              function=utils.cluster_correction))
        cluster_correction_FWE.inputs.t_thresh = self.parameters['height_threshold']
        cluster_correction_FWE.inputs.c_thresh = self.parameters['FWEc']

        cluster_correction_FDR = cluster_correction_FWE.clone(name='cluster_correction_FDR')
        cluster_correction_FDR.inputs.t_thresh = self.parameters['height_threshold']
        cluster_correction_FDR.inputs.c_thresh = self.parameters['FDRc']

        produce_fig_FWE_peak_correction = npe.Node(name='produce_figure_FWE_peak_correction',
                                                   interface=nutil.Function(
                                                       input_names=['nii_file', 'template', 'type_of_correction', 't_thresh', 'c_thresh'],
                                                       output_names=['glass_brain', 'statmap'],
                                                       function=utils.produce_figures))
        produce_fig_FWE_peak_correction.inputs.template = join(dirname(abspath(__file__)), pardir, pardir, 'resources', 'mni_icbm152_t1_tal_nlin_sym_09a.nii.gz')

        produce_fig_FDR_peak_correction = produce_fig_FWE_peak_correction.clone(name='produce_figure_FDR_peak_correction')
        produce_fig_FWE_cluster_correction = produce_fig_FWE_peak_correction.clone(name='produce_figure_FWE_cluster_correction')
        produce_fig_FDR_cluster_correction = produce_fig_FWE_peak_correction.clone(name='produce_figure_FDR_cluster_correction')

        produce_fig_FWE_peak_correction.inputs.type_of_correction = 'FWE'
        produce_fig_FDR_peak_correction.inputs.type_of_correction = 'FDR'
        produce_fig_FWE_cluster_correction.inputs.type_of_correction = 'FWE'
        produce_fig_FDR_cluster_correction.inputs.type_of_correction = 'FDR'

        produce_fig_FWE_peak_correction.inputs.t_thresh = self.parameters['FWEp']
        produce_fig_FDR_peak_correction.inputs.t_thresh = self.parameters['FDRp']
        produce_fig_FWE_cluster_correction.inputs.t_thresh = self.parameters['height_threshold']
        produce_fig_FDR_cluster_correction.inputs.t_thresh = self.parameters['height_threshold']

        produce_fig_FWE_peak_correction.inputs.c_thresh = np.nan
        produce_fig_FDR_peak_correction.inputs.c_thresh = np.nan
        produce_fig_FWE_cluster_correction.inputs.c_thresh = self.parameters['FWEc']
        produce_fig_FDR_cluster_correction.inputs.c_thresh = self.parameters['FDRc']

        # Connection
        # ==========
        self.connect([
            (self.input_node, peak_correction_FWE, [('t_map', 't_map')]),
            (self.input_node, peak_correction_FDR, [('t_map', 't_map')]),
            (self.input_node, cluster_correction_FWE, [('t_map', 't_map')]),
            (self.input_node, cluster_correction_FDR, [('t_map', 't_map')]),

            (peak_correction_FWE, produce_fig_FWE_peak_correction, [('output', 'nii_file')]),
            (peak_correction_FDR, produce_fig_FDR_peak_correction, [('output', 'nii_file')]),
            (cluster_correction_FWE, produce_fig_FWE_cluster_correction, [('output', 'nii_file')]),
            (cluster_correction_FDR, produce_fig_FDR_cluster_correction, [('output', 'nii_file')])
        ])