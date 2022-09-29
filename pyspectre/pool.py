""" Python interface for Cadence Spectre with Parallelization """

import os
import errno
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import pandas as pd
import pynut as pn

import pyspectre as ps

def pool_size(num: int) -> int:
    """
    Determine Poolsize
    """
    return min(num, cpu_count())

def assert_dims( netlists: list[str], includes: list[list[str]] = None
               , raws: list[str] = None
               ) -> (list[str], list[list[str]], list[str]):
    """
    Make sure Pool dimensions align
    """
    num  = len(netlists)

    incs = includes or num * [None]
    raws = raws     or num * [None]

    if num != len(includes):
        raise(ValueError( errno.EINVAL
                        , os.strerror(errno.EINVAL)
                        , '(len(netlist) = {num}) != '
                        + '(len(includes) = {len(includes)}).' ))
    return (netlists, incs, raws)

def assert_lens(list1: list, list2: list) -> bool:
    """
    Assert length of two lists
    """
    length = len(list1) != len(list2)
    if length:
        err_msg = '(len(list1) = {len(list1)}) != (len(list2) = {len(list2)}).'
        raise(ValueError( errno.EINVAL
                        , os.strerror(errno.EINVAL)
                        , err_msg))
    return length

def simulate( netlists: list[str], includes: list[list[str]] = None
            , raws: list[str] = None ) -> pn.NutMeg:
    """
    Passes the given netlists to spectre instances and reads the results in.
    """
    args = zip(*assert_dims(netlists, includes, raws))
    with Pool(pool_size(len(netlists))) as pool:
        rets = pool.starmap(ps.simulate, args)
    return rets

def simulate_netlists( netlists: list[str], includes: list[list[str]] = None
                     , raws: list[str] = None ) -> pn.NutMeg:
    """
    Passes the given netlists to spectre instances and reads the results in.
    """
    args = zip(*assert_dims(netlists, includes, raws))
    with Pool(pool_size(len(netlists))) as pool:
        rets = pool.starmap(ps.simulate_netlist, args)
    return rets

def start_n_sessions( net_path: str, num: int = 1, includes: list[str] = None
                    , raw_path: str = None ) -> list[ps.Session]:
    """
    Start n spectre interactive sessions with same netlist
    """
    args     = zip( num * [net_path], num * [includes], num * [raw_path] )
    with Pool(pool_size(num)) as pool:
        sessions = pool.starmap(ps.start_session, args)
    return sessions

def start_sessions( net_paths: list[str], includes: list[list[str]] = None
                  , raw_paths: list[str] = None ) -> ps.Session:
    """
    Start multiple parallel spectre interactive session
    """
    args = zip(*assert_dims(net_paths, includes, raw_paths))
    with Pool(pool_size(len(net_paths))) as pool:
        rets = pool.starmap(ps.start_session, args)
    return rets

def run_all(sessions: list[ps.Session]) -> list[dict[str, pd.DataFrame]]:
    """
    Run all simulation analyses
    """
    with Pool(pool_size(len(sessions))) as pool:
        rets = pool.map(ps.run_all, sessions)
    return rets

def get_analyses(sessions: list[ps.Session]) -> list[dict[str, str]]:
    """
    Retrieve all simulation analyses from current netlist
    """
    with Pool(pool_size(len(sessions))) as pool:
        rets = pool.map(ps.get_analyses, sessions)
    return rets

def run_analysis( sessions: list[ps.Session], analysis: list[str]
                ) -> list[dict[str, pd.DataFrame]]:
    """
    Run only the given analysis.
    """
    assert_lens(sessions, analysis)
    with Pool(pool_size(len(sessions))) as pool:
        anals = pool.starmap(ps.run_analysis, zip(sessions, analysis))
    return anals

def set_parameters( sessions: list[ps.Session], params: list[dict[str,float]]
                  ) -> list[bool]:
    """
    Change a set of parameters in the given netlists. Returns True if
    successful, False otherwise.
    """
    assert_lens(sessions, params)
    with Pool(pool_size(len(sessions))) as pool:
        rets = pool.starmap(ps.set_parameters, zip(sessions, params))
    return rets

def get_parameters( sessions: list[ps.Session], params: list[list[str]]
                  ) -> list[dict[str, float]]:
    """
    Get parameters in the netlist.
    """
    assert_lens(sessions, params)
    with Pool(pool_size(len(sessions))) as pool:
        params = pool.starmap(ps.get_parameters, zip(sessions, params))
    return params

def stop_sessions(sessions: list[ps.Session]) -> list[bool]:
    """
    Stop list of given spectre interactive sessions
    """
    with Pool(pool_size(len(sessions))) as pool:
        rets = pool.map(ps.stop_session, sessions)
    return rets
