import pyspectre.pool as ps
import pandas as pd
import numpy as np

netlist  = '/home/uhlmanny/.ace/xh035-3V3/op2/mcg_300.scs'
includes = ['/home/uhlmanny/.ace/xh035-3V3/pdk']

## Single Process
n        = 5
sessions = ps.start_n_sessions(netlist, n, includes)
analyses = ps.get_analyses(sessions)
results  = ps.run_all(sessions)
