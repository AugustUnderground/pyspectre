"""Example of the functional pyspectre interface."""
from pathlib import Path
import pyspectre.functional as ps

netlist = Path(__file__).resolve().parent / "example.scs"
includes = ["/opt/pdk/gpdk180_v3.3/models/spectre"]

session = ps.start_session(netlist, includes)
analyses = ps.list_analyses(session)
params = ps.get_parameters(session, ["Wcm2", "Ldp1"])
ps.set_parameters(session, {"Wcm2": 1.5e-6, "Ldp1": 1.0e-6})
ps.get_parameters(session, ["Wcm2", "Ldp1"])
results = ps.run_analysis(session, "tran")
ps.stop_session(session)
