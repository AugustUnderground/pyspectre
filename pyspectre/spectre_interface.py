import os
import yaml
from pathlib import Path
import re
from subprocess import Popen
from tempfile import NamedTemporaryFile
import errno
import warnings
from typing import Dict, Union

import pexpect
from pandas import DataFrame
from pynut import read_raw, plot_dict

from .base_interface import BaseSpectreInterface, Session


def _raw_tmp(net_path: str) -> str:
    """Generate a temporary file path for raw simulation results.

    This function creates a temporary file in the default temporary directory
    with a `.raw` suffix, based on the name of the provided netlist file.

    Parameters
    ----------
    net_path : str
        The path to the netlist file. The basename of this file is used
        as the prefix for the temporary raw file.

    Returns
    -------
    str
        The full path to the created temporary `.raw` file.
    """
    pre = f'{os.path.splitext(os.path.basename(net_path))[0]}'
    suf = '.raw'
    tmp = NamedTemporaryFile(prefix=pre, suffix=suf, delete=False)
    path = tmp.name
    tmp.close()
    return path


def _log_fifo(log_path: str) -> str:
    """Create a FIFO buffer for a Spectre log file.

    This function creates a named pipe (FIFO) at the specified path with a `.log`
    extension. It starts a background process that discards data written to the
    FIFO to prevent blocking during logging.

    Parameters
    ----------
    log_path : str
        The base path for the log file. The `.log` extension will be appended
        to this path to create the FIFO buffer.

    Returns
    -------
    str
        The full path to the created FIFO buffer.
    """
    path = f'{log_path}.log'
    mode = 0o600
    os.mkfifo(path, mode)
    Popen(f'cat {path} > /dev/null 2>&1 &', shell=True)
    return path


def _read_results(raw_file: str, offset: int = 0) -> Dict[str, DataFrame]:
    """Read simulation results from a raw file.

    This function reads simulation results from a specified raw data file and
    returns the results in a structured format. It validates the file's existence
    and readability before processing.

    Parameters
    ----------
    raw_file : str
        The path to the raw simulation results file.
    offset : int, optional
        An offset value to use when reading the raw data (default is 0).

    Returns
    -------
    Dict[str, DataFrame]
        A dictionary where keys are simulation result labels and values are
        corresponding pandas DataFrames containing the data.

    Raises
    ------
    FileNotFoundError
        If the specified raw file does not exist.
    PermissionError
        If the specified raw file is not readable.
    """
    if not os.path.isfile(raw_file):
        raise (FileNotFoundError(errno.ENOENT,
               os.strerror(errno.ENOENT), raw_file))
    if not os.access(raw_file, os.R_OK):
        raise (PermissionError(errno.EACCES, os.strerror(errno.EACCES), raw_file))

    return plot_dict(read_raw(raw_file, off_set=offset))


def _get_yaml(file_name: str) -> dict:
    """Load and return a YAML file.

    Parameters
    ----------
    file_name : str
        The name of the YAML file

    Returns
    -------
    dict
        A dictionary containing the configuration data loaded from the YAML file.

    Raises
    ------
    FileNotFoundError
        If the specified configuration file does not exist.
    """
    config_path = Path(__file__).parent / file_name

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open('r') as file:
        return yaml.safe_load(file)


def _setup_command(path: str):
    """Set up the Spectre command with optional configuration.

    This function constructs the command components for running the Spectre
    simulator. If a configuration file is provided, it customizes the command
    based on the file's content. Defaults are used if the configuration file
    is not found or invalid.

    Parameters
    ----------
    path : str
        Path to the YAML configuration file. If the file is not found or
        invalid, default command components are used.

    Returns
    -------
    tuple
        A tuple containing four components:
        - pre (str): Command prefix (default is an empty string).
        - exe (str): Spectre executable name (default is `'spectre'`).
        - args (list of str): List of command-line arguments (default is
          `['-64', '-format nutbin', '+interactive']`).
        - post (str): Command postfix (default is an empty string).
    """
    pre = ''
    exe = 'spectre'
    args = ['-64', '-format nutbin', '+interactive']
    post = ''
    if path:
        try:
            cfg = _get_yaml(path)
            args = cfg['spectre']['args']
            pre = cfg['spectre']['command_prefix']
            post = cfg['spectre']['command_postfix']
            exe = cfg['spectre']['executable']
        except FileNotFoundError:
            pass
    return pre, exe, args, post


def _run_command(session: Session, command: str) -> bool:
    """Execute an arbitrary SCL command within an active Spectre session.

    This internal function sends a specified command to the Spectre process and checks
    the process's response. It returns `True` if the command was successful based on
    the process's output, and `False` otherwise. If an error is detected, a warning
    is issued indicating that Spectre might have crashed.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session includes the process handle (`repl`) and expected output prompt.
    command : str
        The SCL command to be executed in the Spectre session.

    Returns
    -------
    bool
        `True` if the command was executed successfully (i.e., the expected prompt
        was received after the command). `False` if the command execution did not
        result in the expected output.

    Raises
    ------
    RuntimeError
        If the Spectre session is no longer active (i.e., the process has terminated),
        making it impossible to execute the command.

    Warns
    -----
    RuntimeWarning
        If the Spectre process does not return the expected prompt, indicating that
        the process might have crashed.
    """
    # The command does not crash if a bracket is missing
    if not command.count('(') == command.count(')'):
        raise RuntimeError(
            f"Syntax Error. Check Brackets in command :{command}")

    if session.repl.isalive():
        try:
            session.repl.sendline(command)
            ret = session.repl.expect(session.prompt)
            if ret != 0:
                warnings.warn(f"Spectre might have crashed while executing command: {command}",
                              RuntimeWarning)
            return ret == 0
        except pexpect.exceptions.ExceptionPexpect as e:
            # Handle any unexpected pexpect exceptions
            error_message = f"An error occurred while executing command '{command}': {str(e)}"
            raise RuntimeError(error_message) from e
    else:
        raise RuntimeError(
            "The Spectre session is no longer active. Unable to execute command.")


class SpectreInterface(BaseSpectreInterface):
    """Real implementation of the BaseSpectreInterface for interacting with Cadence Spectre.

    This class provides a concrete implementation of the Spectre interface by establishing
    an interactive session with the Cadence Spectre simulator. It constructs the appropriate
    command line using user-specified netlist, include directories, configuration settings, and
    simulation options (such as APS and Spectre X modes). The implementation handles file path
    expansion, command assembly, permission and existence checks for the netlist, and session
    initialization via the pexpect module.

    Attributes
    ----------
    session : Session
        The simulated session object. Initially set to None and later instantiated
        when start_session is invoked.
    """

    def start_session(self, net_path: str, includes: Union[list[str], None] = None,
                      raw_path: Union[str, None] = None, config_path: str = '',
                      aps_setting: Union[str, None] = None,
                      x_setting: Union[str, None] = None) -> Session:
        offset = 0
        prompt = r'\r\n>\s'
        succ = r'.*\nt'
        fail = r'.*\nnil'
        net = Path(net_path).expanduser()
        raw = Path(raw_path) if raw_path else Path(_raw_tmp(net))
        log = _log_fifo(raw.with_suffix('').as_posix())
        inc = [
            f'-I{Path(i).expanduser().as_posix()}' for i in includes] if includes else []

        command_prefix, spectre_executable, spectre_args, command_postfix \
            = _setup_command(config_path)

        if aps_setting in ["liberal", "moderate", "conservative"]:
            spectre_args += [f" ++aps={aps_setting}"]
        elif x_setting in ["cx", "ax", "mx", "lx", "vx"]:
            spectre_args += [f" +preset={x_setting}"]
        else:
            spectre_args += [" +aps"]

        args = ([spectre_executable] + [net.as_posix()]
                + inc + ['-raw', raw.as_posix(), f'=log {log}']
                + spectre_args)

        if not net.is_file():
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), net)
        if not os.access(net, os.R_OK):
            raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), net)

        command = command_prefix + ' '.join(args) + command_postfix

        repl = pexpect.spawn(command, timeout=2000)
        repl.delaybeforesend = 0.001
        repl.delayafterread = 0.001

        if repl.expect(prompt) != 0:
            raise IOError(errno.EIO, os.strerror(errno.EIO), command)

        self.session = Session(net_path, raw.as_posix(),
                               repl, prompt, succ, fail, offset)

    def run_all(self) -> Dict[str, DataFrame]:
        _run_command(self.session, '(sclRun "all")')
        res = _read_results(self.session.raw_file, offset=self.session.offset)
        self.session.offset = res.get('offset', 0)
        return {n: p for n, p in res.items() if n != 'offset'}

    def run_analysis(self, analysis: str) -> Dict[str, DataFrame]:
        cmd = f'(sclRunAnalysis (sclGetAnalysis "{analysis}"))'
        _run_command(self.session, cmd)
        return _read_results(self.session.raw_file)

    def set_parameter(self, param: str, value: float) -> bool:
        cmd = f'(sclSetAttribute (sclGetParameter (sclGetCircuit "") "{param}") "value" {value})'
        return _run_command(self.session, cmd)

    def get_parameter(self, param: str) -> float:
        cmd = f'(sclGetAttribute (sclGetParameter (sclGetCircuit "") "{param}") "value")'
        _run_command(self.session, cmd)
        return float(self.session.repl.before.decode('utf-8').split('\n')[-1])

    def stop_session(self, remove_raw: bool = False) -> bool:
        if self.session.repl.isalive():
            self.session.repl.sendline('(sclQuit)')
            self.session.repl.wait()
            if self.session.repl.isalive():
                warnings.warn(
                    'spectre refused to exit gracefully, forcing ...', RuntimeWarning)
                self.session.repl.terminate(force=True)
        if remove_raw and os.path.isfile(self.session.raw_file):
            os.remove(self.session.raw_file)
        return not self.session.repl.isalive()

    def list_analyses(self) -> list[str]:
        cmd = '(sclListAnalysis)'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+"([^"]+)"\)', ' '.join(raw_list))

    def list_analysis_types(self) -> list[tuple[str, str]]:
        cmd = '(sclHelp (sclGetAnalysis "ac")'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+"([^"]+)"\)', ' '.join(raw_list))

    def list_instances(self) -> list[str]:
        cmd = '(sclListInstance)'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+"([^"]+)"\)', ' '.join(raw_list))

    def list_nets(self) -> list[str]:
        cmd = '(sclListNet)'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')
        return re.findall(r'"(.*?)"', ' '.join(raw_list))

    def list_circuit_parameters(self) -> list[str]:
        cmd = '(sclListParameter (sclGetCircuit ""))'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+".*?"\)', ' '.join(raw_list))

    def list_analysis_parameters(self, analysis_name: str) -> list[str]:
        cmd = f'(sclListParameter (sclGetAnalysis "{analysis_name}"))'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[2:]
        return re.findall(r'\("([^"]+)"\s+".*?"\)', ' '.join(raw_list))

    def get_analysis_parameter(self, analysis_name: str,
                               parameter_name: str) -> list[tuple[str, str]]:
        cmd = (
            f'(sclListAttribute (sclGetParameter (sclGetAnalysis "{analysis_name}") '
            f'"{parameter_name}"))'
        )
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+"?([^"\)]*)"?\)', ' '.join(raw_list))

    def set_analysis_parameter(self, analysis_name: str, parameter_name: str,
                               attribute_name: str, value: str) -> bool:
        cmd = (
            '(sclSetAttribute '
            f'(sclGetParameter (sclGetAnalysis "{analysis_name}") "{parameter_name}") '
            f'"{attribute_name}" "{value}")'
        )
        return _run_command(self.session, cmd)

    def create_analysis(self, analysis_type: str, analysis_name: str) -> bool:
        cmd = f'(sclCreateAnalysis "{analysis_name}" "{analysis_type}")'
        return _run_command(self.session, cmd)

    def get_circuit_parameter(self, circuit_parameter: str) -> list[tuple[str, str]]:
        cmd = f'(sclListAttribute (sclGetParameter (sclGetCircuit "") "{circuit_parameter}"))'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+"?([^"\)]*)"?\)', ' '.join(raw_list))

    def set_circuit_parameter(self, circuit_parameter: str, attribute_name: str,
                              value: str) -> bool:
        cmd = (
            f'(sclSetAttribute (sclGetParameter (sclGetCircuit "") "{circuit_parameter}") '
            f'"{attribute_name}" "{value}")'
        )
        return _run_command(self.session, cmd)

    def list_instance_parameters(self, instance_name: str) -> list[tuple[str, str]]:
        cmd = f'(sclListParameter (sclGetInstance "{instance_name}"))'
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+".*?"\)', ' '.join(raw_list))

    def get_instance_parameter(self, instance_name: str,
                               instance_parameter: str) -> list[tuple[str, str]]:
        cmd = (
            f'(sclListAttribute (sclGetParameter (sclGetInstance "{instance_name}") '
            f'"{instance_parameter}"))'
        )
        _run_command(self.session, cmd)
        raw_list = self.session.repl.before.decode('utf-8').split('\n')[1:]
        return re.findall(r'\("([^"]+)"\s+"?([^"\)]*)"?\)', ' '.join(raw_list))

    def set_instance_parameter(self, instance_name: str, instance_parameter: str,
                               attribute_name: str, value: str) -> bool:
        cmd = (
            f'(sclSetAttribute (sclGetParameter (sclGetInstance "{instance_name}") '
            f'"{instance_parameter}") "{attribute_name}" "{value}")'
        )
        return _run_command(self.session, cmd)
