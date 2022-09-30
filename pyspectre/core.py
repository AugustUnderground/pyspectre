""" Python interface for Cadence Spectre """

import os
import re
from   subprocess      import run, DEVNULL
from   tempfile        import NamedTemporaryFile
import errno
import warnings
from   collections.abc import Iterable
from   typing          import NamedTuple, NewType
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

def read_results(raw_file: str) -> dict[str, DataFrame]:
    """
    Read simulation results
    """
    if not os.path.isfile(raw_file):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), raw_file))
    if not os.access(raw_file, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), raw_file))

    return plot_dict(read_raw(raw_file))

def simulate( netlist_path: str, includes: Iterable[str] = None
            , raw_path: str = None ) -> dict[str, DataFrame]:
    """
    Passes the given netlist path to spectre and reads the results in.
    """
    net = os.path.expanduser(netlist_path)
    inc = [f'-I{os.path.expanduser(i)}' for i in includes]
    raw = raw_path or raw_tmp(net)
    cmd = ['spectre', '-64', '-format nutbin', f'-raw {raw}', '-log'
          ] + inc + [net]

    if not os.path.isfile(net):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), net))
    if not os.access(net, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), net))

    #ret = os.system(cmd)
    ret = run( cmd
             , check          = False
             , stdin          = DEVNULL
             , stdout         = DEVNULL
             , stderr         = DEVNULL
             , capture_output = False
             , ).returncode

    if ret != 0:
        raise(IOError(errno.EIO, os.strerror(errno.EIO), 'spectre'))

    if not os.path.isfile(raw):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), raw))
    if not os.access(raw, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), raw))

    return read_results(raw)

def simulate_netlist(netlist: str, **kwargs) -> dict[str, DataFrame]:
    """
    Takes a netlist as text, creates a temporary file and simulates it. The
    results are read in and all temp files will be destroyed.
    """
    path = netlist_to_tmp(netlist)
    ret  = simulate(path, **kwargs)
    _    = os.remove(path)
    return ret

REPL    = NewType('REPL', pexpect.spawn)
Session = NamedTuple( 'Session'
                    , [ ( 'net_file', str)
                      , ( 'raw_file', str)
                      , ( 'repl'    , REPL)
                      , ( 'prompt'  , str )
                      , ( 'succ'    , str )
                      , ( 'fail'    , str ) ]
                    ,  )

def start_session( net_path: str, includes: list[str] = None
                 , raw_path: str = None ) -> Session:
    """
    Start spectre interactive session
    """
    prompt = '\r\n>\s'
    succ   = '.*\nt'
    fail   = '.*\nnil'
    net    = os.path.expanduser(net_path)
    raw    = raw_path or raw_tmp(net)
    inc    = [] if not includes else [f'-I{os.path.expanduser(i)}' for i in includes]
    cmd    = 'spectre'
    args   = ['-64', '+interactive', '-format nutbin', f'-raw {raw}', '-log'
             ] + inc + [net]

    if not os.path.isfile(net):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), net))
    if not os.access(net, os.R_OK):
        raise(PermissionError(errno.EACCES, os.strerror(errno.EACCES), net))

    repl   = pexpect.spawn(cmd, args)

    if repl.expect(prompt) != 0:
        raise(IOError(errno.EIO, os.strerror(errno.EIO), cmd))

    return Session(net_path, raw, repl, prompt, succ, fail)

def run_command(session: Session, command: str) -> bool:
    """
    Internal function for running an arbitrary scl command. Returns True or
    false based on what the previous command returned.
    """
    session.repl.sendline(command)
    return session.repl.expect(session.prompt) == 0

def run_all(session: Session) -> dict[str, DataFrame]:
    """
    Run all simulation analyses
    """
    run_command(session, '(sclRun "all")')
    return read_results(session.raw_file)

def get_analyses(session: Session) -> dict[str, str]:
    """
    Retrieve all simulation analyses from current netlist
    """
    cmd = '(sclListAnalysis)'
    run_command(session, cmd)
    out = session.repl.before.decode('utf-8').split('\n')[1:-1]
    return dict([re.search(r'"(.+)"\s*"(.+)"', o).groups() for o in out])

def run_analysis(session: Session, analysis: str) -> dict[str, DataFrame]:
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

def set_parameters(session: Session, params: dict[str, float]) -> bool:
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

def get_parameters(session: Session, params: Iterable[str]) -> dict[str, float]:
    """
    Get a set of parameters in the netlist.
    """
    return {param: get_parameter(session, param) for param in params}

def stop_session(session) -> bool:
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
    return not session.repl.isalive()
