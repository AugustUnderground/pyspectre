from typing import Dict, Union, Iterable
from pandas import DataFrame
from .base_interface import BaseSpectreInterface, Session
import pyspectre.functional as ps
from pathlib import Path


class SpectreInterface(BaseSpectreInterface):
    """Real implementation of the BaseSpectreInterface for interacting with Cadence Spectre.

    This class provides a concrete implementation of the Spectre interface by establishing
    an interactive session with the Cadence Spectre simulator. It constructs the appropriate
    command line using user-specified netlist, include directories, configuration settings, and
    simulation options (such as APS and Spectre X modes). The implementation handles file path
    expansion, command assembly, permission and existence checks for the netlist, and session
    initialization via the pexpect module.

    Attributes
    ----------
    session : Session
        The simulated session object. Initially set to None and later instantiated
        when start_session is invoked.
    """
    session: Session

    def start_session(self, net_path: Union[str, Path], includes: Union[list[str], None] = None,
                      raw_path: Union[str, None] = None, config_path: str = '',
                      aps_setting: Union[str, None] = None,
                      x_setting: Union[str, None] = None):
        if aps_setting in ["liberal", "moderate", "conservative"]:
            args = [f" ++aps={aps_setting}"]
        elif x_setting in ["cx", "ax", "mx", "lx", "vx"]:
            args = [f" +preset={x_setting}"]
        else:
            args = []
        self.session = ps.start_session(net_path, includes, raw_path, config_path,
                                        additional_spectre_args=args)

    def run_all(self) -> Dict[str, DataFrame]:
        return ps.run_all(self.session)

    def get_parameters(self, params: Iterable[str]) -> Dict[str, float]:
        return ps.get_parameters(self.session, params)

    def set_parameters(self, params: Dict[str, float]) -> bool:
        return ps.set_parameters(self.session, params)

    def run_analysis(self, analysis: str) -> Dict[str, DataFrame]:
        return ps.run_analysis(self.session, analysis)

    def set_parameter(self, param: str, value: float) -> bool:
        return ps.set_parameter(self.session, param, value)

    def get_parameter(self, param: str) -> float:
        return ps.get_parameter(self.session, param)

    def stop_session(self, remove_raw: bool = False) -> bool:
        return ps.stop_session(self.session, remove_raw=remove_raw)

    def list_analyses(self) -> list[str]:
        return ps.list_analyses(self.session)

    def list_instances(self) -> list[str]:
        return ps.list_instances(self.session)

    def list_nets(self) -> list[str]:
        return ps.list_nets(self.session)

    def list_analysis_parameters(self, analysis_name: str) -> list[str]:
        return ps.list_analysis_parameters(self.session, analysis_name)

    def get_analysis_parameter(self, analysis_name: str,
                               parameter_name: str) -> list[tuple[str, str]]:
        return ps.get_analysis_parameter(self.session, analysis_name, parameter_name)

    def set_analysis_parameter(self, analysis_name: str, parameter_name: str,
                               attribute_name: str, value: str) -> bool:
        return ps.set_analysis_parameter(self.session, analysis_name, parameter_name,
                                         attribute_name, value)

    def create_analysis(self, analysis_type: str, analysis_name: str) -> bool:
        return ps.create_analysis(self.session, analysis_type, analysis_name)

    def get_circuit_parameter(self, circuit_parameter: str) -> list[tuple[str, str]]:
        return ps.get_circuit_parameter(self.session, circuit_parameter)

    def set_circuit_parameter(self, circuit_parameter: str, attribute_name: str,
                              value: str) -> bool:
        return ps.set_circuit_parameter(self.session, circuit_parameter, attribute_name, value)

    def list_instance_parameters(self, instance_name: str) -> list[tuple[str, str]]:
        return ps.list_instance_parameters(self.session, instance_name)

    def get_instance_parameter(self, instance_name: str,
                               instance_parameter: str) -> list[tuple[str, str]]:
        return ps.get_instance_parameter(self.session, instance_name, instance_parameter)

    def set_instance_parameter(self, instance_name: str, instance_parameter: str,
                               attribute_name: str, value: str) -> bool:
        return ps.set_instance_parameter(self.session, instance_name, instance_parameter,
                                         attribute_name, value)
