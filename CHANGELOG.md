# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.0.4] - 2025-02-25
### Added
- Added module `base_interface.py` as abstract definition of the Python-Spectre interface. Added the Session type to the interface to manage Spectre sessions. This simplifies the PySpectre API and allows object-oriented programming.
- Added module `dummy_interface.py` to implement a dummy interface for software testing without needing Cadence Spectre.
- Added module `spectre_interface` to implement the real interface to Cadence Spectre.

### Changed
- Changed location of `config.yaml` to repository top level directory.

### Removed
- Removed `__main__.py` module 
- Removed `core.py` module

---

## [0.0.3] - 2024-11-11
### Fixed
- Adding default Spectre arguments to Spectre call in function `setup_command` in `core.py` when no config file is specified. 

---

## [0.0.2] - 2024-09-09
### Added
- Added implementation for interactive command `sclListAnalysis`
- Added implementation for interactive command `sclListInstance`
- Added implementation for interactive command `sclListNet`
- Added implementation for interactive command `sclListParameter (sclGetCircuit "")`
- Added implementation for interactive command `sclListParameter (sclGetAnalysis "{analysis_name}")`
- Added implementation for interactive command `sclListAttribute (sclGetParameter (sclGetAnalysis "{analysis_name}") "{parameter_name}")`
- Added implementation for interactive command `sclSetAttribute (sclGetParameter (sclGetAnalysis "{analysis_name}") "{parameter_name}") "{attribute_name}" "{value}"`
- Added implementation for interactive command `sclCreateAnalysis "{analysis_name}" "{analysis_type}"`
- Added implementation for interactive command `sclListAttribute (sclGetParameter (sclGetCircuit "") "{circuit_parameter}")`
- Added implementation for interactive command `sclSetAttribute (sclGetParameter (sclGetCircuit "") "{circuit_parameter}") "{attribute_name}" "{value}"`
- Added implementation for interactive command `sclListParameter (sclGetInstance "{instance_name}")`
- Added implementation for interactive command `sclListAttribute (sclGetParameter (sclGetInstance "{instance_name}") "{instance_parameter}")`
- Added implementation for interactive command `sclSetAttribute (sclGetParameter (sclGetInstance "{instance_name}") "{instance_parameter}") "{attribute_name}" "{value}"`
- Added Jupyter notebook for demonstration of interactive interface
- Added docstrings in numpydoc format
- Added configuration file
- Added CHANGELOG file
- Added CONTRIBUTORS file

### Changed
- Added exceptions to `start_session()` in `core.py`
- Added exceptions to `run_command()` in `core.py`

### Fixed
- Fixed linting to PEP8.

---

## [0.0.1] - 2022-09-29
### Added
- Initial release of the project by Yannick Uhlmann.
- Basic functionality for Python interface to Spectre.
- README documentation and setup.

---

> **Note**: Dates should follow the format `YYYY-MM-DD`.

