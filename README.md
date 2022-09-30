# PySpectre

Python interface to Cadence Spectre.

## Dependencies

- [pynut](https://github.com/augustunderground/pynut).
- [Cadence Spectre](https://www.cadence.com/en_US/home/tools/custom-ic-analog-rf-design/circuit-simulation/spectre-simulation-platform.html), the `spectre` command should be available in you shell

## Installation

```sh
$ pip install git+https://github.com/augustunderground/pyspectre.git
```

## Example

Simulate a netlist and retrieve simulation results:

```python
import pyspectre as ps

netlist  = 'path/to/netlist.scs'
includes = ['path/to/pdk/libs']

results  = ps.simulate(netlist, includes)
```

Start an interactive session:

```python
import pyspectre as ps

netlist  = 'path/to/netlist.scs'
includes = ['path/to/pdk/libs']

# Start Interactive session
session  = ps.start_session(netlist, includes)

# Retrieve simulation analyses defined in the netlist
analyses = ps.get_analyses(session)

# Get values for parameters defined in the netlist
params   = ps.get_parameters(session, ['Wcm2', 'Ld'])

# Set netlist parameters
ps.set_parameters(session, {'Wcm2': 2.0e-6, 'Ld': 1.0e-6})

# Simulate
results  = ps.run_all(session)

# End Interactive session
ps.stop_session(session)
```

Check `./test/example.py` for more.
