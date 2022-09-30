import pyspectre as ps
import pandas as pd
import numpy as np

netlist  = '~/.ace/xh035-3V3/op2/mcg_300.scs'
includes = ['~/.ace/xh035-3V3/pdk']

## Single Process
session  = ps.start_session(netlist, includes)
analyses = ps.get_analyses(session)
results  = ps.run_all(session)

## Single Process
n        = 5
sessions = ps.start_session(n * [netlist], n * [includes])
analyses = ps.get_analyses(sessions)
results  = ps.run_all(sessions)
