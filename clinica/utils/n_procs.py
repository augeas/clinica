
import click

def update_parallelize_info(plugin_args):
    """Performs some checks of the number of threads given in parameters,
    given the number of CPUs of the machine in which clinica is running.
    We force the use of plugin MultiProc

    Author: Arnaud Marcoux"""
    import select
    import sys
    from multiprocessing import cpu_count

    from clinica.utils.stream import cprint

    # count number of CPUs
    n_cpu = cpu_count()
    # timeout value: max time allowed to decide how many thread
    # to run in parallel (sec)
    timeout = 15

    # Use this var to know in the end if we need to ask the user
    # an other number
    ask_user = False

    try:
        # if no --n_procs arg is used, plugin_arg is None
        # so we need a try / except block
        n_thread_cmdline = plugin_args["n_procs"]
        if n_thread_cmdline > n_cpu:
            cprint(
                msg=(
                    f"You are trying to run clinica with a number of threads ({n_thread_cmdline}) superior to your "
                    f"number of CPUs ({n_cpu})."
                ),
                lvl="warning",
            )
            ask_user = True
    except TypeError:
        cprint(
            msg=f"You did not specify the number of threads to run in parallel (--n_procs argument).",
            lvl="warning",
        )
        cprint(
            msg=(
                f"Computation time can be shorten as you have {n_cpu} CPUs on this computer. "
                f"We recommend using {n_cpu-1} threads."
            ),
            lvl="warning",
        )
        ask_user = True

    if ask_user:
        n_procs = click.prompt(
            text="How many threads do you want to use?",
            default=max(1, n_cpu - 1),
            show_default=True,
        )
        click.echo(
            f"Number of threads set to {n_procs}. You may set the --n_procs argument "
            "to disable this message for future calls."
        )
        if plugin_args:
            plugin_args["n_procs"] = n_procs
        else:
            plugin_args = {"n_procs": n_procs}

    return plugin_args
