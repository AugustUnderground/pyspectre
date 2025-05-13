"""Improved example of using the pyspectre functional interface with print statements.
Demonstrates starting/stopping a session, listing analyses, querying and setting parameters,
and running a transient analysis.
"""

import sys
from pathlib import Path
import pyspectre.functional as ps


def main():
    # Path to the Spectre netlist
    netlist = Path(__file__).resolve().parent / "example.scs"
    if not netlist.exists():
        print(f"Error: Netlist file not found: {netlist}")
        sys.exit(1)

    # Additional include directories for Spectre models
    includes = ["/opt/pdk/gpdk180_v3.3/models/spectre"]

    session = None
    try:
        # Start a pyspectre session
        session = ps.start_session(netlist, includes)
        print("Session started.")

        # List available analyses
        analyses = ps.list_analyses(session)
        print("Available analyses:", analyses)

        # Read default parameter values
        parameters = ["Wcm2", "Ldp1"]
        defaults = ps.get_parameters(session, parameters)
        print("Default parameters:", defaults)

        # Update parameters
        new_values = {"Wcm2": 1.5e-6, "Ldp1": 1.0e-6}
        ps.set_parameters(session, new_values)
        updated = ps.get_parameters(session, parameters)
        print("Updated parameters:", updated)

        # Run transient analysis
        results = ps.run_analysis(session, "tran")
        print("Transient analysis results:", results)

    except Exception as e:
        print("An error occurred during functional interface usage:", e)
        sys.exit(1)

    finally:
        if session is not None:
            try:
                ps.stop_session(session)
                print("Session stopped.")
            except Exception as e:
                print("Warning: failed to stop session:", e)

    print("Example script completed successfully.")


if __name__ == "__main__":
    main()
