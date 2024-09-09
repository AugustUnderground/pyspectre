# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added

### Changed
  
### Fixed


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

