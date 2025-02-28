import random
from typing import List, Dict, Union, Iterable
from pandas import DataFrame
from .base_interface import BaseSpectreInterface, Session


class DummySpectreInterface(BaseSpectreInterface):
    """Dummy implementation of the BaseSpectreInterface.

    This class provides a stubbed implementation of the Spectre interface for testing
    and development purposes. Instead of launching an actual Cadence Spectre session,
    it simulates the behavior by creating a dummy Session object. This allows developers
    to test integration and code flow without requiring the full Spectre environment.

    Attributes
    ----------
    session : Session
        The simulated session object. Initially set to None and later instantiated
        when start_session is invoked.
    """

    def __init__(self):
        self.session = None

    def start_session(self, net_path: str, includes: Union[List[str], None] = None,
                      raw_path: Union[str, None] = None, config_path: str = '') -> Session:
        self.session = Session(net_file=net_path, raw_file=raw_path or "dummy.raw", repl=None,
                               prompt=None, succ=None, fail=None, offset=None)
        return self.session

    def stop_session(self, remove_raw: bool = False) -> bool:
        self.session = None
        return True

    def run_simulation(self) -> Dict[str, DataFrame]:
        return {
            "analysis1": DataFrame({"time": [0, 1, 2],
                                    "voltage": [random.random() for _ in range(3)]}),
            "analysis2": DataFrame({"frequency": [1e3, 1e4, 1e5],
                                    "gain": [random.random() for _ in range(3)]}),
        }

    def run_analysis(self, analysis: str) -> Dict[str, DataFrame]:
        return {
            analysis: DataFrame({"param": [0, 1, 2], "value": [
                                random.random() for _ in range(3)]})
        }

    def set_parameter(self, param: str, value: float) -> bool:
        return True

    def set_parameters(self, params: Dict[str, float]) -> bool:
        return True

    def get_parameter(self, param: str) -> float:
        return random.random()

    def get_parameters(self, params: Iterable[str]) -> Dict[str, float]:
        return {param: random.random() for param in params}

    def list_analyses(self) -> List[str]:
        return ["ac", "dc", "tran", "noise"]

    def list_analysis_parameters(self, analysis_name: str) -> List[str]:
        return ["start", "stop", "step", "accuracy"]

    def set_analysis_parameter(self, analysis_name: str, parameter_name: str, attribute_name: str,
                               value: str) -> bool:
        return True

    def get_analysis_parameter(self, analysis_name: str, parameter_name: str
                               ) -> List[tuple[str, str]]:
        return [("attr1", "value1"), ("attr2", "value2")]

    def create_analysis(self, analysis_type: str, analysis_name: str) -> bool:
        return True

    def list_nets(self) -> List[str]:
        return ["net1", "net2", "net3"]

    def list_instances(self) -> List[str]:
        return ["instance1", "instance2", "instance3"]

    def list_circuit_parameters(self) -> List[str]:
        return ["param1", "param2", "param3"]

    def get_circuit_parameter(self, circuit_parameter: str) -> List[tuple[str, str]]:
        return [("attr1", "value1"), ("attr2", "value2")]

    def set_circuit_parameter(self, circuit_parameter: str, attribute_name: str,
                              value: str) -> bool:
        return True

    def list_instance_parameters(self, instance_name: str) -> List[tuple[str, str]]:
        return [("param1", "value1"), ("param2", "value2")]

    def get_instance_parameter(self, instance_name: str, instance_parameter: str
                               ) -> List[tuple[str, str]]:
        return [("attr1", "value1"), ("attr2", "value2")]

    def set_instance_parameter(self, instance_name: str, instance_parameter: str,
                               attribute_name: str, value: str) -> bool:
        return True
