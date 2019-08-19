import sys
import subprocess
import os
from abc import ABC

from grid import utils as gr_utils


class BaseDeployment(ABC):
    """ Abstract Class used to instantiate generic attributes for other deployment classes. """

    def __init__(self, env_vars, verbose: bool = True):
        """
        Args:
            env_vars: Environment vars used to configure component
            verbose: Used to define level of verbosity
            logs: list of logs used in deploy process
            commands: list of commands used in deploy process
        """
        self.env_vars = env_vars
        self.verbose = verbose
        self.logs = list()
        self.commands = list()

    def deploy_on_heroku(self):
        """ Method used to deploy component on heroku platform. """
        raise RuntimeError("Heroku deployment not specified!")

    def deploy_on_container(self):
        """ Method used to deploy component using docker containers. """
        raise RuntimeError("Container deployment not specified!")

    def _check_dependency(
        self,
        lib="git",
        check="usage:",
        error_msg="Error: please install git.",
        verbose=False,
    ):
        """ This method checks if the environment have a specific dependency.
            Args:
                dependency_lib : libs that will be verified.
                check: specific string to check if app was installed.
                error_msg: If not installed, raise an Exception with this.
                verbose: Used to define level of verbosity.
            Raises:
                Exception: if not installed, raise a standard Exception
        """
        if verbose:
            sys.stdout.write("\tChecking for " + str(lib) + " dependency...")
        o = gr_utils.exec_os_cmd(lib)
        if check not in o:
            raise Exception(error_msg)
        if verbose:
            print("DONE!")

    def _execute(self, cmd):
        """ Execute a specific bash command and return the result.
            Args:
                cmd: specific bash command.
            Raises:
                subprocess_exception: Raises an specific subprocess exception
        """
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

    def _run_commands_in(
        self, commands, logs, tmp_dir="tmp", cleanup=True, verbose=False
    ):
        """ Run sequentially all commands and logs stored in our list of commands/logs.
            Args:
                commands: list of commands.
                logs: list of logs.
                tmp_dir: directory used execute these commands.
                cleanup: flag to choose if tmp_dir will be maintained.
                verbose: Used to define level of verbosity.
            Returns:
                outputs: Output message for each command.
        """
        assert len(commands) == len(logs)
        gr_utils.exec_os_cmd("mkdir " + tmp_dir)

        outputs = list()

        cmd = ""
        for i in range(len(commands)):

            if verbose:
                print(logs[i] + "...")

            cmd = "cd " + str(tmp_dir) + "; " + commands[i] + "; cd ..;"
            o = gr_utils.exec_os_cmd(cmd)
            outputs.append(str(o))

            if verbose:
                print("\t" + str(o).replace("\n", "\n\t"))

        if cleanup:
            gr_utils.exec_os_cmd("rm -rf " + tmp_dir)

        return outputs
