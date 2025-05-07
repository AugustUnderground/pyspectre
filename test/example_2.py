"""Improved example of using the pyspectre SpectreInterface with print statements.
Demonstrates listing analyses, querying and setting parameters, and running a transient analysis.
"""

import sys
from pathlib import Path
from pyspectre import SpectreInterface


def main():
    # Path to the Spectre netlist
    netlist = Path(__file__).resolve().parent / "example.scs"
    if not netlist.exists():
        print(f"Error: Netlist file not found: {netlist}")
        sys.exit(1)

    # Additional include directories for Spectre models
    includes = ["/opt/pdk/gpdk180_v3.3/models/spectre"]

    # Create and configure the Spectre interface
    try:
        with SpectreInterface(netlist, includes=includes, aps_setting="liberal") as ps:
            # List available analyses
            analyses = ps.list_analyses()
            print("Available analyses:", analyses)

            # Read default parameter values
            parameters = ["Wcm2", "Ldp1"]
            defaults = ps.get_parameters(parameters)
            print("Default parameters:", defaults)

            # Update parameters
            new_values = {"Wcm2": 1.5e-6, "Ldp1": 1.0e-6}
            ps.set_parameters(new_values)
            updated = ps.get_parameters(parameters)
            print("Updated parameters:", updated)

            # Run transient analysis
            results = ps.run_analysis("tran")
            print("Transient analysis results:", results)

    except Exception as e:
        print("An error occurred while running SpectreInterface:", e)
        sys.exit(1)

    print("Example script completed successfully.")


if __name__ == "__main__":
    main()
