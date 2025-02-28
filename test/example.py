from pyspectre import SpectreInterface
ps = SpectreInterface()

netlist = './test/example.scs'
includes = ['/opt/pdk/gpdk180_v3.3/models/spectre']

# Batch
results = ps.simulate(netlist, includes)

# Interactive
session = ps.start_session(netlist, includes)
analyses = ps.get_analyses()
params = ps.get_parameters(['Wcm2', 'Ldp1'])
ps.set_parameters({'Wcm2': 1.5e-6, 'Ldp1': 1.0e-6})
ps.get_parameters(['Wcm2', 'Ldp1'])
results = ps.run_all()
ps.stop_session()
