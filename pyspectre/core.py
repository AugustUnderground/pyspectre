""" Python interface for Cadence Spectre """

import os
import re
import subprocess
from   subprocess      import run, DEVNULL, Popen
from   tempfile        import NamedTemporaryFile
import errno
import warnings
from   collections.abc import Iterable
from   typing          import NamedTuple, NewType, List, Dict, Iterable

from   dataclasses     import dataclass
import pexpect
from   pandas          import DataFrame
from   pynut           import read_raw, plot_dict

def netlist_to_tmp(netlist: str) -> str:
    """
    Write a netlist to a temporary file
    """
    tmp  = NamedTemporaryFile(mode = 'w', suffix = '.scs', delete = False)
    path = tmp.name
    tmp.write(netlist)
    tmp.close()
    return path

def raw_tmp(net_path: str) -> str:
    """
    Raw simulation results in /tmp
    """
    pre  = f'{os.path.splitext(os.path.basename(net_path))[0]}'
    suf  = '.raw'
    tmp  = NamedTemporaryFile(prefix = pre, suffix = suf, delete = False)
    path = tmp.name
    tmp.close()
    return path

def log_fifo(log_path: str) -> str:
    """
    Create fifo buffer for spectre log file
    """
    path  = f'{log_path}.log'
    mode = 0o600
    os.mkfifo(path, mode)
    Popen(f'cat {path} > /dev/null 2>&1 &', shell=True)
    return path

def read_results(raw_file: str, offset: int = 0) -> Dict[str, DataFrame]:
    """
    Read simulation results
    """
    if not os.path.isfile(raw_file):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), raw_file))
    if not os.access(raw_file, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), raw_file))

    return plot_dict(read_raw(raw_file, off_set = offset))

def simulate( netlist_path: str, includes: List[str] = None
            , raw_path: str = None, log_path: str = None
            ) -> Dict[str, DataFrame]:
    """
    Passes the given netlist path to spectre and reads the results in.
    """
    net = os.path.expanduser(netlist_path)
    inc = [f'-I{os.path.expanduser(i)}' for i in includes] if includes else []
    raw = raw_path or raw_tmp(net)
    log = f'{net}.log' if not log_path else f'{log_path}'
    #log_path = log
    # These individual arguments cannot be combined with the argument options, those are not recognized
    cmd = ['spectre', '-64', '-format', 'nutbin', '-raw', f'{raw}', '+log', f'{log}'] + inc + [net]

    if not os.path.isfile(net):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), net))
    if not os.access(net, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), net))

    #ret = os.system(cmd)
    ret = run( cmd
             , check         =True
             , stdin         =DEVNULL
             , stdout        =True
             , stderr        =True
             , capture_output=False
             , ).returncode

    if ret != 0:
        if log_path is not None:
            with open(log_path, 'r', encoding='utf-8') as log_handle:
                print(log_handle.read())
        else:
            print( '\n\n\n+++++++++++++++++++++++++++++'
                   'log_path was not specified, '
                 + f'Using Default log file name {log}\n'
                   f'+++++++++++++++++++++++++++++++++')

        #raise(IOError( errno.EIO, os.strerror(errno.EIO)
        #             , f'spectre returned with non-zero exit code: {ret}'
        #             , ))
    if not os.path.isfile(raw):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), raw))
    if not os.access(raw, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), raw))

    return {n: p for n, p in read_results(raw).items() if n != 'offset'}

def simulate_netlist(netlist: str, **kwargs) -> Dict[str, DataFrame]:
    """
    Takes a netlist as text, creates a temporary file and simulates it. The
    results are read in and all temp files will be destroyed.
    """
    path = netlist_to_tmp(netlist)
    ret  = simulate(path, **kwargs)
    _    = os.remove(path)
    return ret

REPL    = NewType('REPL', pexpect.spawn)

@dataclass
class Session:
    """ Interactive Spectre Session """
    net_file: str
    raw_file: str
    repl    : REPL
    prompt  : str
    succ    : str
    fail    : str
    offset  : int

def start_session( net_path: str, includes: List[str] = None
                 , raw_path: str = None)-> Session:
    """
    Start spectre interactive session
    """
    offset = 0
    prompt = '\r\n>\s'
    succ   = '.*\nt'
    fail   = '.*\nnil'
    net    = os.path.expanduser(net_path)
    raw    = raw_path or raw_tmp(net)
    log    = log_fifo(os.path.splitext(raw)[0])
    inc    = [] if not includes else [f'-I{os.path.expanduser(i)}' for i in includes]
    cmd    = 'spectre'
    args   = ['-64', '+interactive', '-format', 'nutbin', '-raw', f'{raw}', f'+log', f'{log}'] + inc + [net]

    if not os.path.isfile(net):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), net))
    if not os.access(net, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), net))
    # Spectre interactive session host handle ?
    repl   = pexpect.spawn(cmd, args, timeout = 120)
    repl.delaybeforesend = 0.001
    repl.delayafterread  = 0.001

    if repl.expect(prompt) != 0:
        raise(IOError(errno.EIO, os.strerror(errno.EIO), cmd))

    return Session(net_path, raw, repl, prompt, succ, fail, offset)


def run_command(session: Session, command: str) -> bool:
    """
    Internal function for running an arbitrary scl command. Returns True or
    false based on what the previous command returned.
    """
    session.repl.sendline(command)
    ret = session.repl.expect(session.prompt)

    if ret != 0:
        warnings.warn('spectre might have crashed ... ', RuntimeWarning)

    return ret == 0

def run_all(session: Session) -> Dict[str, DataFrame]:
    """
    Run all simulation analyses
    """
    run_command(session, '(sclRun "all")')
    res = read_results(session.raw_file, offset = session.offset)
    session.offset = res.get('offset', 0)
    return {n: p for n,p in res.items() if n != 'offset'}

def get_analyses(session: Session) -> Dict[str, str]:
    """
    Retrieve all simulation analyses from current netlist
    """
    cmd = '(sclListAnalysis)'
    run_command(session, cmd)
    out = session.repl.before.decode('utf-8').split('\n')[1:-1]
    return dict([re.search(r'"(.+)"\s*"(.+)"', o).groups() for o in out])

def run_analysis(session: Session, analysis: str) -> Dict[str, DataFrame]:
    """
    Run only the given analysis.
    """
    cmd = f'(sclRunAnalysis (sclGetAnalysis "{analysis}"))'
    run_command(session, cmd)
    return read_results(session.raw_file)

def set_parameter(session: Session, param: str, value: float) -> bool:
    """
    Change a parameter in the netlist. Returns True if successful, False
    otherwise.
    """
    cmd = f'(sclSetAttribute (sclGetParameter (sclGetCircuit "") "{param}") "value" {value})'
    return run_command(session, cmd)

def set_parameters(session: Session, params: Dict[str, float]) -> bool:
    """
    Set a list of parameters
    """
    return all(set_parameter(session, p, v) for p,v in params.items())

def get_parameter(session: Session, param: str) -> float:
    """
    Get a parameter in the netlist.
    """
    cmd = f'(sclGetAttribute (sclGetParameter (sclGetCircuit "") "{param}") "value")'
    run_command(session, cmd)
    return float(session.repl.before.decode('utf-8').split('\n')[-1])

def get_parameters(session: Session, params: Iterable[str]) -> Dict[str, float]:
    """
    Get a set of parameters in the netlist.
    """
    return {param: get_parameter(session, param) for param in params}

def stop_session(session, remove_raw: bool = False) -> bool:
    """
    Quit spectre interactive session and close terminal
    """
    if session.repl.isalive():
        session.repl.sendline('(sclQuit)')
        session.repl.wait()
        if session.repl.isalive():
            warnings.warn( 'spectre refused to exit gracefully, forcing ...'
                         , RuntimeWarning )
            session.repl.terminate(force = True)
    if remove_raw and os.path.isfile(session.raw_file):
        os.remove(session.raw_file)
    return not session.repl.isalive()
