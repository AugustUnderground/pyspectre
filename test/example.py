import pyspectre as ps
import pandas as pd
import numpy as np

netlist = './test/example.scs'
includes = ['/opt/pdk/gpdk180_v3.3/models/spectre']

## One-Shot
results = ps.simulate(netlist, includes)

## Single Process
session  = ps.start_session(netlist, includes)
analyses = ps.get_analyses(session)
params   = ps.get_parameters(session, ['Wcm2', 'Ldp1'])
ps.set_parameters(session, {'Wcm2': 1.5e-6, 'Ldp1': 1.0e-6})
results  = ps.run_all(session)

## Parallel Jobs
n        = 5
sessions = ps.start_session(n * [netlist], n * [includes])
analyses = ps.get_analyses(sessions)
params   = ps.get_parameters(sessions, n * [['Wcm2', 'Ldp1']])
ps.set_parameters(sessions, n * [{'Wcm2': 2.0e-6, 'Ldp1': 1.0e-6}])
results  = ps.run_all(sessions)
