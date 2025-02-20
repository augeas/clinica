from typing import Optional

import click

import clinica.pydra.engine_utils as pydra_utils
import clinica.pydra.statistics_volume_correction.pipeline as pydra_statistics_volume_correction
from clinica.pipelines import cli_param
from clinica.pipelines.engine import clinica_pipeline

pipeline_name = "pydra-statistics-volume-correction"


@clinica_pipeline
@click.command(name=pipeline_name)
@cli_param.argument.caps_directory
@click.argument("t_map", type=str)
@click.argument("height_threshold", type=float)
@click.argument("FWEp", type=float)
@click.argument("FDRp", type=float)
@click.argument("FWEc", type=float)
@click.argument("FDRc", type=float)
@cli_param.option_group.pipeline_specific_options
@cli_param.option_group.option(
    "-nc",
    "--n_cuts",
    default=8,
    show_default=True,
    help="Number of cuts along each direction",
)
@cli_param.option_group.common_pipelines_options
@cli_param.option.working_directory
@cli_param.option.n_procs
def cli(
    caps_directory: str,
    t_map: str,
    height_threshold: float,
    fwep: float,
    fdrp: float,
    fwec: float,
    fdrc: float,
    n_cuts: int = 8,
    working_directory: Optional[str] = None,
    n_procs: Optional[int] = None,
) -> None:
    """Statistical correction of statistics-volume pipeline.

       T_MAP is the name of the T statistic map used for the correction.

       HEIGHT_THRESHOLD is the T value corresponding to an uncorrected p-value of 0.001.

       FWEp is the Family-Wise Error peak threshold.

       FDRp is the False Discovery Rate peak threshold.

       Finally, FWEc and FDRc stand for the respective correction parameters.

    Prerequisite: You have to perform the statistics-volume pipeline before running this pipeline.

    https://aramislab.paris.inria.fr/clinica/docs/public/latest/Pipelines/Stats_Volume/
    """

    parameters = {
        "t_map": t_map,
        "height_threshold": height_threshold,
        "FWEp": fwep,
        "FDRp": fdrp,
        "FWEc": fwec,
        "FDRc": fdrc,
        "n_cuts": n_cuts,
    }

    pipeline = pydra_statistics_volume_correction.build_core_workflow(
        name="statistics-volume-correction-pydra",
        input_dir=None,
        output_dir=caps_directory,
        parameters=parameters,
    )
    pydra_utils.run(pipeline, n_procs)


if __name__ == "__main__":
    cli()
