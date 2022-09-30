import pyspectre as ps
import pandas as pd
import numpy as np

netlist  = '~/.ace/xh035-3V3/op2/mcg_300.scs'
includes = ['~/.ace/xh035-3V3/pdk']

## One-Shot
results = ps.simulate(netlist, includes)

## Single Process
session  = ps.start_session(netlist, includes)
analyses = ps.get_analyses(session)
params   = ps.get_parameters(session, ['Wcm2', 'Ld'])
ps.set_parameters(session, {'Wcm2': 2.0e-6, 'Ld': 1.0e-6})
results  = ps.run_all(session)

## Parallel Jobs
n        = 5
sessions = ps.start_session(n * [netlist], n * [includes])
analyses = ps.get_analyses(sessions)
params   = ps.get_parameters(sessions, n * [['Wcm2', 'Ld']])
ps.set_parameters(sessions, n * [{'Wcm2': 2.0e-6, 'Ld': 1.0e-6}])
results  = ps.run_all(sessions)
