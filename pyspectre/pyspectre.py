""" Python interface for Cadence Spectre """

import os
import re
import tempfile
import errno
import warnings
from typing import NamedTuple
import pexpect
import pandas as pd
import pynut as pn

def netlist_to_tmp(netlist: str) -> str:
    """
    Write a netlist to a temporary file
    """
    with tempfile.NamedTemporaryFile( mode   = 'w'
                                    , suffix = '.scs'
                                    , delete = False
                                    , ) as tmp:
        path = tmp.name
        _    = tmp.write(netlist)
        _    = tmp.close
    return path

def simulate( netlist_path: str, includes: list[str] = None
            , raw_path: str = None ) -> pn.NutMeg:
    """
    Passes the given netlist path to spectre and reads the results in.
    """
    inc = '' if not includes else '-I' + ' -I'.join(includes)
    raw = raw_path or f'{os.path.splitext(os.path.basename(netlist_path))[0]}.raw'
    cmd = f'spectre -64 -format nutbin -raw {raw} -log {inc} {netlist_path}'
    ret = os.system(cmd)

    if ret != 0:
        raise(IOError( errno.EIO, os.strerror(errno.EIO), 'spectre'))

    if not os.path.isfile(raw):
        raise(FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), raw))

    return raw

def simulate_netlist(netlist: str, **kwargs) -> pn.NutMeg:
    """
    Takes a netlist as text, creates a temporary file and simulates it. The
    results are read in and all temp files will be destroyed.
    """
    path = netlist_to_tmp(netlist)
    ret  = simulate(path, **kwargs)
    _    = os.remove(path)
    return ret

Session = NamedTuple( 'Session'
                    , [ ( 'net_file', str)
                      , ( 'raw_file', str)
                      , ( 'repl', pexpect.spawn)
                      , ( 'prompt', str )
                      , ( 'succ', str )
                      , ( 'fail', str ) ]
                    ,  )

def start_session( net_path: str, includes: list[str] = None
                 , raw_path: str = None ) -> Session:
    """
    Start spectre interactive session
    """
    if not os.path.isfile(net_path):
        raise(FileNotFoundError( errno.ENOENT
                               , os.strerror(errno.ENOENT)
                               , net_path ))

    prompt = '\r\n>\s'
    succ   = '.*\nt'
    fail   = '.*\nnil'
    raw    = raw_path or f'{os.path.splitext(os.path.basename(net_path))[0]}.raw'
    inc    = [] if not includes else [f'-I{i}' for i in includes]
    cmd    = 'spectre'
    args   = ['-64', '+interactive', '-format nutbin', f'-raw {raw}', '-log'
             ] + inc + [net_path]
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

def read_results(session: Session) -> dict[str, pd.DataFrame]:
    """
    Read simulation results
    """
    if not os.path.isfile(session.raw_file):
        raise(FileNotFoundError( errno.ENOENT
                               , os.strerror(errno.ENOENT)
                               , session.raw_file ))

    return pn.plot_dict(pn.read_raw(session.raw_file))

def run_all(session: Session) -> dict[str, pd.DataFrame]:
    """
    Run all simulation analyses
    """
    run_command(session, '(sclRun "all")')
    return read_results(session)

def get_analyses(session: Session) -> dict[str, str]:
    """
    Retrieve all simulation analyses from current netlist
    """
    cmd = '(sclListAnalysis)'
    run_command(session, cmd)
    out = session.repl.before.decode('utf-8').split('\n')[1:-1]
    return dict([re.search(r'"(.+)"\s*"(.+)"', o).groups() for o in out])

def run_analysis(session: Session, analysis: str) -> dict[str, pd.DataFrame]:
    """
    Run only the given analysis.
    """
    cmd = f'(sclRunAnalysis (sclGetAnalysis "{analysis}"))'
    run_command(session, cmd)
    return read_results(session)

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
    return run_command(session, cmd)

def get_parameters(session: Session, params: list[str]) -> dict[str, float]:
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
