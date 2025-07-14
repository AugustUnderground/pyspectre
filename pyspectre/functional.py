""" Python interface for Cadence Spectre """

import os
import yaml
from pathlib import Path
import re
from subprocess import run, DEVNULL, Popen
from tempfile import NamedTemporaryFile
import errno
import warnings
from typing import NewType, List, Dict, Iterable, Union, Optional

from dataclasses import dataclass
import pexpect
from pandas import DataFrame
from pynut import read_raw, plot_dict


def netlist_to_tmp(netlist: str) -> str:
    """Write a netlist to a temporary file

    Parameters
    ----------
    netlist : str
        The contents of the netlist file.

    Returns
    -------
    str
        The full path to the created file.
    """
    tmp = NamedTemporaryFile(mode='w', suffix='.scs', delete=False)
    path = tmp.name
    tmp.write(netlist)
    tmp.close()
    return path


def raw_tmp(net_path: Union[str, Path]) -> str:
    """Generate a temporary file path for raw simulation results.

    This function creates a temporary file in the default temporary directory
    with a `.raw` suffix, based on the name of the provided netlist file.

    Parameters
    ----------
    net_path : Union[str, Path]
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


def log_fifo(log_path: str) -> str:
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


def get_yaml(file_name: str) -> Dict:
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


def read_results(raw_file: str, offset: int = 0) -> Dict[str, DataFrame]:
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


def simulate(netlist_path: str, includes: Optional[List[str]] = [], raw_path: str = "",
             log_path: str = "", log_silent=True) -> Dict[str, DataFrame]:
    """
    Passes the given netlist path to spectre and reads the results in.
    """
    net = os.path.expanduser(netlist_path)
    inc = [f'-I{os.path.expanduser(i)}' for i in includes] if includes else []
    raw = raw_path or raw_tmp(net)
    if log_path and log_silent:
        log_option = ['=log', log_path]
    elif log_path and not log_silent:
        log_option = ['+log', log_path]
    elif (not log_path) and (not log_silent):
        log_option = ['-log']
    else:
        buf = log_fifo(f'{net}')
        log_option = ['=log', buf]

    cmd = ['spectre', '-64', '-format', 'nutbin', '-raw', f'{raw}'
           ] + log_option + inc + [net]

    if not os.path.isfile(net):
        raise (FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), net))
    if not os.access(net, os.R_OK):
        raise (PermissionError(errno.EACCES, os.strerror(errno.EACCES), net))

    # ret = os.system(cmd)
    ret = run(cmd, check=True, stdin=DEVNULL, stdout=DEVNULL,
              stderr=DEVNULL, capture_output=False, ).returncode

    if ret != 0:
        if log_path:
            with open(log_path, 'r', encoding='utf-8') as log_handle:
                print(log_handle.read())
        else:
            raise (IOError(errno.EIO, os.strerror(errno.EIO),
                   f'spectre returned with non-zero exit code: {ret}', ))
    if not os.path.isfile(raw):
        raise (FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), raw))
    if not os.access(raw, os.R_OK):
        raise (PermissionError(errno.EACCES, os.strerror(errno.EACCES), raw))

    return {n: p for n, p in read_results(raw).items() if n != 'offset'}


def simulate_netlist(netlist: str, **kwargs) -> Dict[str, DataFrame]:
    """
    Takes a netlist as text, creates a temporary file and simulates it. The
    results are read in and all temp files will be destroyed.
    """
    path = netlist_to_tmp(netlist)
    ret = simulate(path, **kwargs)
    os.remove(path)
    return ret


REPL = NewType('REPL', pexpect.spawn)


@dataclass
class Session:
    """Represents an interactive Spectre session.

    This class encapsulates the state and relevant information for an active
    Spectre session. It includes details about the netlist and raw output files,
    the instance managing the interaction with Spectre,
    and the prompts and patterns used for command success and failure detection.

    Attributes
    ----------
    net_file : Union[str, Path]
        The path to the netlist file used in the Spectre session.
    raw_file : str
        The path to the raw output file generated by the Spectre session.
    repl : REPL
        An instance of the `REPL` class that handles the interactive communication
        with the Spectre process. This includes sending commands and receiving output.
    prompt : str
        The expected prompt string used to detect when the Spectre process is ready
        to accept the next command.
    succ : str
        The regular expression pattern used to identify successful command execution
        in the Spectre session.
    fail : str
        The regular expression pattern used to identify failed command execution
        in the Spectre session.
    offset : int
        The current offset used for reading results from the raw output file. This
        helps track the position in the file for incremental reads after each analysis.
    """
    net_file: Union[str, Path]
    raw_file: str
    repl: pexpect.spawn
    prompt: str
    succ: str
    fail: str
    offset: int


def setup_command(path: str):
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
            cfg = get_yaml(path)
            args = cfg['spectre']['args']
            pre = cfg['spectre']['command_prefix']
            post = cfg['spectre']['command_postfix']
            exe = cfg['spectre']['executable']
        except FileNotFoundError:
            pass
    return pre, exe, args, post


def start_session(net_path: Union[str, Path], includes: Union[list[str], None] = None,
                  raw_path: Union[str, None] = None, config_path: str = '',
                  additional_spectre_args: list[str] = []) -> Session:
    """Start a Spectre interactive session.

    Parameters
    ----------
    net_path : Union[str, Path]
        The file path to the netlist that will be used in the Spectre session.
        This file must exist and be readable.
    includes : List[str], optional
        A list of directory paths to be included with the `-I` option in the
        Spectre command. Each path will be expanded if necessary. Defaults to None.
    raw_path : str, optional
        The file path where the raw output will be stored. If not provided,
        a temporary raw file path is generated based on the netlist file name.
        Defaults to None.
    config_path : str, optional
        Path to a yaml file that configures the spectre executable. See
        `config.yaml` as example.
    Returns
    -------
    Session
        An instance of the `Session` class, representing the active Spectre
        session, which includes the session's configuration and the active
        process handle.

    Raises
    ------
    FileNotFoundError
        If the netlist file specified by `net_path` does not exist.

    PermissionError
        If the netlist file specified by `net_path` is not readable.

    IOError
        If the Spectre session fails to start due to an input/output error
        with the command execution.
    """

    offset = 0
    prompt = r'\r\n>\s'
    succ = r'.*\nt'
    fail = r'.*\nnil'
    net = Path(net_path).expanduser()
    raw = Path(raw_path) if raw_path else Path(raw_tmp(net))
    log = log_fifo(raw.with_suffix('').as_posix())
    inc = [
        f'-I{Path(i).expanduser().as_posix()}' for i in includes] if includes else []

    command_prefix, spectre_executable, spectre_args, command_postfix \
        = setup_command(config_path)

    args = ([spectre_executable] + [net.as_posix()]
            + inc + ['-raw', raw.as_posix(), '=log', log]
            + spectre_args + additional_spectre_args)

    if not net.is_file():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), net)
    if not os.access(net, os.R_OK):
        raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), net)

    command = command_prefix + ' '.join(args) + command_postfix

    repl = pexpect.spawn(command, timeout=120)
    repl.delaybeforesend = 0.001
    repl.delayafterread = 0.001

    if repl.expect(prompt) != 0:
        raise IOError(errno.EIO, os.strerror(errno.EIO), command)

    return Session(net_path, raw.as_posix(), repl, prompt, succ, fail, offset)


def run_command(session: Session, command: str) -> bool:
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


def run_all(session: Session) -> Dict[str, DataFrame]:
    """Run all simulation analyses in the Spectre session and retrieve the results.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.

    Returns
    -------
    Dict[str, DataFrame]
        A dictionary where the keys are the names of the analyses, and the values
        are pandas DataFrames containing the results of each analysis.
    """
    run_command(session, '(sclRun "all")')
    res = read_results(session.raw_file, offset=session.offset)
    offset_value = res.get('offset', 0)
    if isinstance(offset_value, int):
        session.offset = offset_value
    else:
        session.offset = 0
    return {n: p for n, p in res.items() if n != 'offset'}


def run_analysis(session: Session, analysis: str) -> Dict[str, DataFrame]:
    """Run a specific analysis in the active Spectre session.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    analysis : str
        The name of the analysis to be run. This should correspond to an analysis
        that is recognized by the Spectre session.

    Returns
    -------
    Dict[str, DataFrame]
        A dictionary where the keys are the names of the analysis results, and the
        values are pandas DataFrames containing the data from each result.
    """
    cmd = f'(sclRunAnalysis (sclGetAnalysis "{analysis}"))'
    run_command(session, cmd)
    return read_results(session.raw_file)


def set_parameter(session: Session, param: str, value: float) -> bool:
    """
    Change the value of a netlist parameter in the Spectre session.

    This function sends a command to the Spectre session to update the value of
    a specified parameter in the netlist. It returns `True` if the parameter
    value was successfully changed, and `False` otherwise.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    param : str
        The name of the netlist parameter whose value is to be changed.
    value : float
        The new value to be assigned to the specified parameter.

    Returns
    -------
    bool
        `True` if the parameter value was successfully updated, `False` if the
        command failed or the parameter could not be changed.
    """
    cmd = f'(sclSetAttribute (sclGetParameter (sclGetCircuit "") "{param}") "value" {value})'
    return run_command(session, cmd)


def set_parameters(session: Session, params: Dict[str, float]) -> bool:
    """Set the values for a list of netlist parameters in the Spectre session.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    params : Dict[str, float]
        A dictionary where the keys are the names of the netlist parameters and the
        values are the new values to be assigned to those parameters.

    Returns
    -------
    bool
        `True` if all parameters were successfully updated, `False` if any of the
        parameter updates failed.
    """
    return all(set_parameter(session, p, v) for p, v in params.items())


def get_parameter(session: Session, param: str) -> float:
    """Retrieve the value of a specified netlist parameter in the Spectre session.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    param : str
        The name of the netlist parameter whose value is to be retrieved.

    Returns
    -------
    float
        The current value of the specified netlist parameter.
    """
    cmd = f'(sclGetAttribute (sclGetParameter (sclGetCircuit "") "{param}") "value")'
    run_command(session, cmd)
    return float(session.repl.before.decode('utf-8').split('\n')[-1])


def get_parameters(session: Session, params: Iterable[str]) -> Dict[str, float]:
    """Retrieve the values of a set of netlist parameters in the Spectre session.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    params : Iterable[str]
        An iterable of strings, where each string is the name of a netlist parameter
        whose value is to be retrieved.

    Returns
    -------
    Dict[str, float]
        A dictionary where the keys are the names of the specified parameters and
        the values are the corresponding parameter values retrieved from the netlist.
    """
    return {param: get_parameter(session, param) for param in params}


def stop_session(session, remove_raw: bool = False) -> bool:
    """Quit the Spectre interactive session and close the terminal.

    This function attempts to gracefully quit the Spectre interactive session by sending
    the `(sclQuit)` command. If Spectre refuses to exit gracefully, it forces termination
    of the session. Optionally, it can also remove the raw output file associated with
    the session.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    remove_raw : bool, optional
        If `True`, the raw output file associated with the session will be deleted
        after the session is stopped. Defaults to `False`.

    Returns
    -------
    bool
        `True` if the session was successfully terminated (whether gracefully or by force),
        `False` otherwise.

    Warns
    -----
    RuntimeWarning
        If the session refuses to exit gracefully and is forcibly terminated.
    """
    if session.repl.isalive():
        session.repl.sendline('(sclQuit)')
        session.repl.wait()
        if session.repl.isalive():
            warnings.warn(
                'spectre refused to exit gracefully, forcing ...', RuntimeWarning)
            session.repl.terminate(force=True)
    if remove_raw and os.path.isfile(session.raw_file):
        os.remove(session.raw_file)
    return not session.repl.isalive()


def list_analyses(session: Session) -> list[str]:
    """Retrieve all simulation analyses from the current interactive Spectre session.

    This function sends a command to the Spectre session to list all available
    simulation analyses. It then parses the command output and returns a list
    of analysis names.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.

    Returns
    -------
    list[str]
        A list of strings where each string is the name of a simulation analysis
        available in the current Spectre session.
    """
    cmd = '(sclListAnalysis)'
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[1:]
    return re.findall(r'\("([^"]+)"\s+"([^"]+)"\)', ' '.join(raw_list))


def list_instances(session: Session) -> list[str]:
    """Retrieve a list of all components inthe circuit.

    This function sends a command to the Spectre session to list all available
    instances. It then parses the command output and returns a list of instance
    names.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.

    Returns
    -------
    list[str]
        A list of strings where each string is the name of an component or instance available
        in the current Spectre session.
    """
    cmd = '(sclListInstance)'
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[1:]
    return re.findall(r'\("([^"]+)"\s+"([^"]+)"\)', ' '.join(raw_list))


def list_nets(session: Session) -> list[str]:
    """Retrieve a list of all nets in the circuit.

    This function sends a command to the Spectre session to list all available
    nets. It then parses the command output and returns a list of net names.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.

    Returns
    -------
    list[str]
        A list of strings where each string is the name of a net available
        in the current Spectre session.
    """
    cmd = '(sclListNet)'
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')
    return re.findall(r'"(.*?)"', ' '.join(raw_list))


def list_analysis_parameters(session: Session, analysis_name: str) -> list[str]:
    """Retrieve a list of parameters for a specified analysis in the current Spectre session.

    This function sends a command to the Spectre session to list all parameters
    associated with a specified analysis. It then parses the command output
    and returns a list of parameter names.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    analysis_name : str
        The name of the analysis for which to list the parameters. This should be
        a valid analysis name within the current Spectre session.

    Returns
    -------
    list[str]
        A list of strings where each string is the name of a parameter associated
        with the specified analysis in the current Spectre session.
    """
    cmd = f'(sclListParameter (sclGetAnalysis "{analysis_name}"))'
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[2:]
    return re.findall(r'\("([^"]+)"\s+".*?"\)', ' '.join(raw_list))


def get_analysis_parameter(session, analysis_name, parameter_name) -> list[tuple[str, str]]:
    """Retrieve the attributes and their values for a specified parameter in a given analysis.

    This function sends a command to the Spectre session to list all attributes
    associated with a specific parameter of a specified analysis. It then parses
    the command output and returns a list of tuples, where each tuple contains
    an attribute name and its corresponding value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    analysis_name : str
        The name of the analysis for which the parameter attributes are to be retrieved.
        This should be a valid analysis name within the current Spectre session.
    parameter_name : str
        The name of the parameter whose attributes and values are to be retrieved.
        This should be a valid parameter name within the specified analysis.

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples where each tuple contains:
        - The name of the attribute (str).
        - The value of the attribute (str).
    """
    cmd = (
        f'(sclListAttribute (sclGetParameter (sclGetAnalysis "{analysis_name}") '
        f'"{parameter_name}"))'
    )
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[1:]
    return re.findall(r'\("([^"]+)"\s+"?([^"\)]*)"?\)', ' '.join(raw_list))


def set_analysis_parameter(session: Session, analysis_name: str, parameter_name: str,
                           attribute_name: str, value: str) -> bool:
    """Set the value of a specific attribute for a parameter in a given analysis.

    This function sends a command to the Spectre session to set the value of a
    specified attribute for a parameter within a particular analysis. The command
    is constructed based on the provided analysis name, parameter name, attribute
    name, and the new value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    analysis_name : str
        The name of the analysis that contains the parameter to be modified. This
        should be a valid analysis name within the current Spectre session.
    parameter_name : str
        The name of the parameter whose attribute is to be set. This should be a
        valid parameter name within the specified analysis.
    attribute_name : str
        The name of the attribute to be modified. This should be a valid attribute
        name for the specified parameter.
    value : str
        The new value to set for the specified attribute.

    Returns
    -------
    bool
        `True` if the command to set the attribute was successfully executed,
        `False` otherwise.
    """
    cmd = (
        f'(sclSetAttribute (sclGetParameter (sclGetAnalysis "{analysis_name}") "{parameter_name}") '
        f'"{attribute_name}" "{value}")'
    )
    return run_command(session, cmd)


def create_analysis(session: Session, analysis_type: str, analysis_name: str) -> bool:
    """Create a new analysis in the Spectre session.

    To see the available analysis types check the file reference.yaml.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    analysis_type : str
        The type of analysis to be created. This should be a valid analysis type
        recognized by the Spectre session.
    analysis_name : str
        The name to assign to the new analysis. This name must be unique within
        the session.

    Returns
    -------
    bool
        `True` if the analysis was successfully created, `False` if the command
        failed to execute.
    """
    cmd = f'(sclCreateAnalysis "{analysis_name}" "{analysis_type}")'
    return run_command(session, cmd)


def get_circuit_parameter(session: Session, circuit_parameter: str) -> list[tuple[str, str]]:
    """Retrieve the attributes and their values for a specified circuit parameter.

    This function sends a command to the Spectre session to list all attributes
    associated with a specified circuit parameter. It then parses the command output
    and returns a list of tuples, where each tuple contains an attribute name
    and its corresponding value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    circuit_parameter : str
        The name of the circuit parameter whose attributes and values are to be retrieved.
        This should be a valid circuit parameter name within the current Spectre session.

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples where each tuple contains:
        - The name of the attribute (str).
        - The value of the attribute (str).
    """
    cmd = f'(sclListAttribute (sclGetParameter (sclGetCircuit "") "{circuit_parameter}"))'
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[1:]
    return re.findall(r'\("([^"]+)"\s+"?([^"\)]*)"?\)', ' '.join(raw_list))


def set_circuit_parameter(session: Session, circuit_parameter: str, attribute_name: str,
                          value: str) -> bool:
    """Set the value of a specific attribute for a circuit parameter in the current Spectre session.

    This function sends a command to the Spectre session to set the value of a
    specified attribute for a circuit parameter. The command is constructed based
    on the provided circuit parameter name, attribute name, and the new value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    circuit_parameter : str
        The name of the circuit parameter whose attribute is to be set. This should
        be a valid circuit parameter name within the current Spectre session.
    attribute_name : str
        The name of the attribute to be modified. This should be a valid attribute
        name for the specified circuit parameter.
    value : str
        The new value to set for the specified attribute.

    Returns
    -------
    bool
        `True` if the command to set the attribute was successfully executed,
        `False` otherwise.
    """
    cmd = (
        f'(sclSetAttribute (sclGetParameter (sclGetCircuit "") "{circuit_parameter}") '
        f'"{attribute_name}" "{value}")'
    )
    return run_command(session, cmd)


def list_instance_parameters(session: Session, instance_name: str) -> list[tuple[str, str]]:
    """Retrieve the parameters and their values for a specified instance.

    This function sends a command to the Spectre session to list all parameters
    associated with a specific instance. It then parses the command output and
    returns a list of tuples, where each tuple contains a parameter name and its
    corresponding value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    instance_name : str
        The name of the instance whose parameters are to be retrieved. This should
        be a valid instance name within the current Spectre session.

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples where each tuple contains:
        - The name of the parameter (str).
        - The value of the parameter (str).
    """
    cmd = f'(sclListParameter (sclGetInstance "{instance_name}"))'
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[1:]
    return re.findall(r'\("([^"]+)"\s+".*?"\)', ' '.join(raw_list))


def get_instance_parameter(session: Session, instance_name: str,
                           instance_parameter: str) -> list[tuple[str, str]]:
    """Retrieve the attributes and their values for a specified parameter of an instance.

    This function sends a command to the Spectre session to list all attributes
    associated with a specific parameter of a given instance. It then parses the
    command output and returns a list of tuples, where each tuple contains an
    attribute name and its corresponding value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    instance_name : str
        The name of the instance whose parameter attributes are to be retrieved.
        This should be a valid instance name within the current Spectre session.
    instance_parameter : str
        The name of the parameter whose attributes and values are to be retrieved.
        This should be a valid parameter name within the specified instance.

    Returns
    -------
    list[tuple[str, str]]
        A list of tuples where each tuple contains:
        - The name of the attribute (str).
        - The value of the attribute (str).
    """
    cmd = (
        f'(sclListAttribute (sclGetParameter (sclGetInstance "{instance_name}") '
        f'"{instance_parameter}"))'
    )
    run_command(session, cmd)
    raw_list = session.repl.before.decode('utf-8').split('\n')[1:]
    return re.findall(r'\("([^"]+)"\s+"?([^"\)]*)"?\)', ' '.join(raw_list))


def set_instance_parameter(session: Session, instance_name: str, instance_parameter: str,
                           attribute_name: str, value: str) -> bool:
    """Set the value of a specific attribute for a parameter of an instance.

    This function sends a command to the Spectre session to set the value of a
    specified attribute for a parameter within a particular instance. The command
    is constructed based on the provided instance name, parameter name, attribute
    name, and the new value.

    Parameters
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    instance_name : str
        The name of the instance that contains the parameter to be modified. This
        should be a valid instance name within the current Spectre session.
    instance_parameter : str
        The name of the parameter whose attribute is to be set. This should be a
        valid parameter name within the specified instance.
    attribute_name : str
        The name of the attribute to be modified. This should be a valid attribute
        name for the specified parameter.
    value : str
        The new value to set for the specified attribute.

    Returns
    -------
    bool
        `True` if the command to set the attribute was successfully executed,
        `False` otherwise.
    """
    cmd = (
        f'(sclSetAttribute (sclGetParameter (sclGetInstance "{instance_name}") '
        f'"{instance_parameter}") "{attribute_name}" "{value}")'
    )
    return run_command(session, cmd)
