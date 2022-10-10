""" Python interface for Cadence Spectre """

from collections.abc       import Iterable
from multiprocessing       import cpu_count
from multiprocessing.dummy import Pool
from typing                import Callable, Union
from pandas                import DataFrame
from .                     import core

def _run(num: int, fun: Callable, *args):
    """
    Run function in parallel or not
    """
    num_par = min(num, cpu_count())
    if num > 1:
        with Pool(num_par) as pool:
            res = pool.starmap(fun, zip(*args))
    else:
        res = fun(*args)
    return res

def simulate( net_path: Union[str,Iterable[str]]
            , includes: Union[Iterable[str], Iterable[Iterable[str]]] = None
            , raw_path: Union[str,Iterable[str]] = None
            ) -> Union[ dict[str, DataFrame]
                      , Iterable[dict[str, DataFrame]] ]:
    """
    Passes the given netlists to spectre instances and reads the results in.
    """
    num = 1 if isinstance(net_path, str) else len(net_path)
    return _run(num, core.simulate, net_path, includes, raw_path)

def simulate_netlists( netlist: Union[str,Iterable[str]]
                     , includes: Union[Iterable[str], Iterable[Iterable[str]]] = None
                     , raw_path: Union[str,Iterable[str]] = None
                     ) -> Union[ dict[str, DataFrame]
                               , Iterable[dict[str, DataFrame]] ]:
    """
    Passes the given netlists to spectre instances and reads the results in.
    """
    num = 1 if isinstance(netlist, str) else len(netlist)
    return _run(num, core.simulate_netlist, netlist, includes, raw_path)

def start_session( net_path: Union[str, Iterable[str]]
                 , includes: Union[Iterable[str], Iterable[Iterable[str]]] = None
                 , raw_path: Union[str, Iterable[str]] = None
                 ) -> Union[core.Session, Iterable[core.Session]]:
    """
    Start spectre interactive session(s)
    """
    num  = 1 if isinstance(net_path, str) else len(net_path)
    incs = num * [includes] if (num > 1 and includes and isinstance(includes[0], str)) \
            else (num * [None] if num > 1 else None)
            # else (includes if includes and len(includes) == num else num * [None])
    raws = num * [raw_path] if (num > 1 and isinstance(raw_path, str)) \
            else (num * [None] if (not raw_path and num > 1) else raw_path)
    return _run(num, core.start_session, net_path, incs, raws)

# def start_n_sessions( net_path: str, includes: Iterable[str] = None
#                     , raw_path: str = None, num: int = 1
#                     ) -> Iterable[core.Session]:
#     """
#     Start n parallel sessions with the same netlist
#     """
#     nets = num * [net_path] if num > 1 else net_path
#     incs = num * [includes] if (includes and num > 1) else \
#             (num * [None] if num > 1 else includes)
#     raws = num * [raw_path] if num > 1 else raw_path
#     return start_session(nets, incs, raws)

def run_all( session: Union[core.Session, Iterable[core.Session]]
           ) -> Union[ dict[str, DataFrame]
                     , Iterable[dict[str, DataFrame]] ]:
    """
    Run all simulation analyses
    """
    num = 1 if isinstance(session, core.Session) else len(session)
    return _run(num, core.run_all, session)

def get_analyses( session: core.Session
                ) -> Union[dict[str, str], Iterable[dict[str, str]]]:
    """
    Retrieve all simulation analyses from current netlist
    """
    num = 1 if isinstance(session, core.Session) else len(session)
    return _run(num, core.get_analyses, session)

def run_analysis( session: Union[core.Session, Iterable[core.Session]]
                , analysis: Union[str, Iterable[str]]
                ) -> Union[ dict[str, DataFrame]
                          , Iterable[dict[str, DataFrame]] ]:
    """
    Run only the given analysis.
    """
    num = 1 if isinstance(session, core.Session) else len(session)
    return _run(num, core.run_analysis, session, analysis)

def set_parameters( session: Union[core.Session, Iterable[core.Session]]
                  , params: Union[dict[str, float], Iterable[dict[str, float]]]
                  ) -> Union[bool, Iterable[bool]]:
    """
    Set a list of parameters
    """
    num = 1 if isinstance(session, core.Session) else len(session)
    return _run(num, core.set_parameters, session, params)

def get_parameters( session: Union[core.Session, Iterable[core.Session]]
                  , params: Union[Iterable[str], Iterable[Iterable[str]]]
                  ) -> Union[dict[str, float], Iterable[dict[str, float]]]:
    """
    Get a parameter in the netlist.
    """
    num = 1 if isinstance(session, core.Session) else len(session)
    return _run(num, core.get_parameters, session, params)

def stop_session( session: Union[core.Session,Iterable[core.Session]]
                , remove_raw: bool = True
                ) -> Union[bool, Iterable[bool]]:
    """
    Stop spectre interactive session(s)
    """
    num = 1 if isinstance(session, core.Session) else len(session)
    rem  = num * [remove_raw] if num > 1 else remove_raw
    return _run(num, core.stop_session, session, rem)
