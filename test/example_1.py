"""Example of the functional pyspectre interface."""

import pyspectre.functional as ps

netlist = './test/example.scs'
includes = ['/opt/pdk/gpdk180_v3.3/models/spectre']

session = ps.start_session(netlist, includes)
analyses = ps.get_analyses(session)
params = ps.get_parameters(session, ['Wcm2', 'Ldp1'])
ps.set_parameters(session, {'Wcm2': 1.5e-6, 'Ldp1': 1.0e-6})
ps.get_parameters(session, ['Wcm2', 'Ldp1'])
results = ps.run_all(session)
ps.stop_session(session)
