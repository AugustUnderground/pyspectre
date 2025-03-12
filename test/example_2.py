"""Example of the object oriented pyspectre interface."""

from pyspectre import SpectreInterface

netlist = './test/example.scs'
includes = ['/opt/pdk/gpdk180_v3.3/models/spectre']

with SpectreInterface(netlist, includes) as ps:
    analyses = ps.list_analyses()
    params = ps.get_parameters(['Wcm2', 'Ldp1'])
    ps.set_parameters({'Wcm2': 1.5e-6, 'Ldp1': 1.0e-6})
    ps.get_parameters(['Wcm2', 'Ldp1'])
    results = ps.run_analysis("tran")
