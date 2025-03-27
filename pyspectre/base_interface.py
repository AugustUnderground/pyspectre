from abc import ABC, abstractmethod
from typing import Dict, Union, Iterable, List, Optional
from typing_extensions import Literal
from pandas import DataFrame
from pyspectre.functional import Session
from pathlib import Path


class BaseSpectreInterface(ABC):
    """Abstract Base Class for interfacing with Cadence Spectre.

    This defines the standard API for interacting with Spectre, including
    session management, simulation execution, and parameter handling.

    Attributes
    ----------
    session : Session
        An instance of the `Session` class representing the active Spectre session.
        The session contains necessary information, including the raw output file
        and the current offset for reading results.
    """
    session: Session

    @abstractmethod
    def start_session(self, net_path: Union[str, Path], includes: Union[list[str], None] = None,
                      raw_path: Union[str, None] = None, config_path: str = '',
                      aps_setting: Union[str, None] = None,
                      x_setting: Union[str, None] = None) -> None:
        """Start a Spectre interactive session.

        Parameters
        ----------
        net_path : Union[str, Path]
            The file path to the netlist that will be used in the Spectre session.
            This file must exist and be readable.
        includes : List[str], optional
            A list of directory paths to be included with the `-I` option in the
            Spectre command. Each path will be expanded if necessary. Defaults to None.
        raw_path : str, optional
            The file path where the raw output will be stored. If not provided,
            a temporary raw file path is generated based on the netlist file name.
            Defaults to None.
        config_path : str, optional
            Path to a yaml file that configures the spectre executable. See
            `config.yaml` as example.
        aps_setting : str, optional
            If the value is not set the APS ++ mode is disabled.
            The ++aps mode uses a different time-step control
            algorithm compared to Spectre. This can result in improved performance,
            while satisfying error tolerances and constraints.
            Possible settings for the errpreset in all transient analyses
            are 'liberal', 'moderate' or 'conservative'.
        x_setting : str, optional
            If the value is not set the Spectre X mode is disabled.
            The most accurate mode is 'cx', and the highest performing mode is 'vx'.
            Possible values are 'cx', 'ax', 'mx', 'lx', 'vx'.

        Raises
        ------
        FileNotFoundError
            If the netlist file specified by `net_path` does not exist.

        PermissionError
            If the netlist file specified by `net_path` is not readable.

        IOError
            If the Spectre session fails to start due to an input/output error
            with the command execution.
        """
        pass

    @abstractmethod
    def stop_session(self, remove_raw: bool = False) -> bool:
        """Quit the Spectre interactive session and close the terminal.

        This function attempts to gracefully quit the Spectre interactive session by sending
        the `(sclQuit)` command. If Spectre refuses to exit gracefully, it forces termination
        of the session. Optionally, it can also remove the raw output file associated with
        the session.

        Parameters
        ----------
        remove_raw : bool, optional
            If `True`, the raw output file associated with the session will be deleted
            after the session is stopped. Defaults to `False`.

        Returns
        -------
        bool
            `True` if the session was successfully terminated (whether gracefully or by force),
            `False` otherwise.

        Warns
        -----
        RuntimeWarning
            If the session refuses to exit gracefully and is forcibly terminated.
        """
        pass

    def __init__(self, net_path: Union[str, Path], includes: Optional[List[str]] = None,
                 raw_path: Optional[str] = None, config_path: str = '',
                 aps_setting: Optional[str] = None, x_setting: Optional[str] = None):
        """Initialize the SpectreInterface with parameters necessary for starting a session."""
        self.net_path = net_path
        self.includes = includes
        self.raw_path = raw_path
        self.config_path = config_path
        self.aps_setting = aps_setting
        self.x_setting = x_setting

    def __enter__(self) -> "BaseSpectreInterface":
        """Enter the runtime context and start the Spectre session.

        The subclass implementation of start_session will be called.
        """
        self.start_session(
            net_path=self.net_path,
            includes=self.includes,
            raw_path=self.raw_path,
            config_path=self.config_path,
            aps_setting=self.aps_setting,
            x_setting=self.x_setting
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> Literal[False]:
        """Exit the runtime context and stop the Spectre session.

        Parameters
        ----------
        exc_type, exc_value, traceback:
            Exception details if one occurred.

        Returns
        -------
        Literal[False]
            False so that any exception is propagated.
        """
        self.stop_session(remove_raw=False)
        return False

    @abstractmethod
    def run_analysis(self, analysis: str) -> Dict[str, DataFrame]:
        """Run a specific analysis in the active Spectre session.

        Parameters
        ----------
        analysis : str
            The name of the analysis to be run. This should correspond to an analysis
            that is recognized by the Spectre session.

        Returns
        -------
        Dict[str, DataFrame]
            A dictionary where the keys are the names of the analysis results, and the
            values are pandas DataFrames containing the data from each result.
        """
        pass

    @abstractmethod
    def set_parameter(self, param: str, value: float) -> bool:
        """Change the value of a netlist parameter in the Spectre session.

        This function sends a command to the Spectre session to update the value of
        a specified parameter in the netlist. It returns `True` if the parameter
        value was successfully changed, and `False` otherwise.

        Parameters
        ----------
        param : str
            The name of the netlist parameter whose value is to be changed.
        value : float
            The new value to be assigned to the specified parameter.

        Returns
        -------
        bool
            `True` if the parameter value was successfully updated, `False` if the
            command failed or the parameter could not be changed.
        """
        pass

    @abstractmethod
    def set_parameters(self, params: Dict[str, float]) -> bool:
        """Set the values for a list of netlist parameters in the Spectre session.

        Parameters
        ----------
        params : Dict[str, float]
            A dictionary where the keys are the names of the netlist parameters and the
            values are the new values to be assigned to those parameters.

        Returns
        -------
        bool
            `True` if all parameters were successfully updated, `False` if any of the
            parameter updates failed.
        """
        pass

    @abstractmethod
    def get_parameter(self, param: str) -> float:
        """Retrieve the value of a specified netlist parameter in the Spectre session.

        Parameters
        ----------
        param : str
            The name of the netlist parameter whose value is to be retrieved.

        Returns
        -------
        float
            The current value of the specified netlist parameter.
        """
        pass

    @abstractmethod
    def get_parameters(self, params: Iterable[str]) -> Dict[str, float]:
        """Retrieve the values of a set of netlist parameters in the Spectre session.

        Parameters
        ----------
        params : Iterable[str]
            An iterable of strings, where each string is the name of a netlist parameter
            whose value is to be retrieved.

        Returns
        -------
        Dict[str, float]
            A dictionary where the keys are the names of the specified parameters and
            the values are the corresponding parameter values retrieved from the netlist.
        """
        pass

    @abstractmethod
    def list_analyses(self) -> list[str]:
        """Retrieve all simulation analyses from the current interactive Spectre session.

        This function sends a command to the Spectre session to list all available
        simulation analyses. It then parses the command output and returns a list
        of analysis names.

        Returns
        -------
        list[str]
            A list of strings where each string is the name of a simulation analysis
            available in the current Spectre session.
        """
        pass

    @abstractmethod
    def list_instances(self) -> list[str]:
        """Retrieve a list of all components inthe circuit.

        This function sends a command to the Spectre session to list all available
        instances. It then parses the command output and returns a list of instance
        names.

        Returns
        -------
        list[str]
            A list of strings where each string is the name of an component or instance available
            in the current Spectre session.
        """
        pass

    @abstractmethod
    def list_nets(self) -> list[str]:
        """Retrieve a list of all nets in the circuit.

        This function sends a command to the Spectre session to list all available
        nets. It then parses the command output and returns a list of net names.

        Returns
        -------
        list[str]
            A list of strings where each string is the name of a net available
            in the current Spectre session.
        """
        pass

    @abstractmethod
    def list_analysis_parameters(self, analysis_name: str) -> list[str]:
        """Retrieve a list of parameters for a specified analysis in the current Spectre session.

        This function sends a command to the Spectre session to list all parameters
        associated with a specified analysis. It then parses the command output
        and returns a list of parameter names.

        Parameters
        ----------
        analysis_name : str
            The name of the analysis for which to list the parameters. This should be
            a valid analysis name within the current Spectre session.

        Returns
        -------
        list[str]
            A list of strings where each string is the name of a parameter associated
            with the specified analysis in the current Spectre session.
        """
        pass

    @abstractmethod
    def get_analysis_parameter(self, analysis_name, parameter_name
                               ) -> list[tuple[str, str]]:
        """Retrieve the attributes and their values for a specified parameter in a given analysis.

        This function sends a command to the Spectre session to list all attributes
        associated with a specific parameter of a specified analysis. It then parses
        the command output and returns a list of tuples, where each tuple contains
        an attribute name and its corresponding value.

        Parameters
        ----------
        analysis_name : str
            The name of the analysis for which the parameter attributes are to be retrieved.
            This should be a valid analysis name within the current Spectre session.
        parameter_name : str
            The name of the parameter whose attributes and values are to be retrieved.
            This should be a valid parameter name within the specified analysis.

        Returns
        -------
        list[tuple[str, str]]
            A list of tuples where each tuple contains:
            - The name of the attribute (str).
            - The value of the attribute (str).
        """
        pass

    @abstractmethod
    def set_analysis_parameter(self, analysis_name: str, parameter_name: str,
                               attribute_name: str, value: str) -> bool:
        """Set the value of a specific attribute for a parameter in a given analysis.

        This function sends a command to the Spectre session to set the value of a
        specified attribute for a parameter within a particular analysis. The command
        is constructed based on the provided analysis name, parameter name, attribute
        name, and the new value.

        Parameters
        ----------
        analysis_name : str
            The name of the analysis that contains the parameter to be modified. This
            should be a valid analysis name within the current Spectre session.
        parameter_name : str
            The name of the parameter whose attribute is to be set. This should be a
            valid parameter name within the specified analysis.
        attribute_name : str
            The name of the attribute to be modified. This should be a valid attribute
            name for the specified parameter.
        value : str
            The new value to set for the specified attribute.

        Returns
        -------
        bool
            `True` if the command to set the attribute was successfully executed,
            `False` otherwise.
        """
        pass

    @abstractmethod
    def create_analysis(self, analysis_type: str, analysis_name: str) -> bool:
        """Create a new analysis in the Spectre session.

        To see the available analysis types check the file reference.yaml.

        Parameters
        ----------
        analysis_type : str
            The type of analysis to be created. This should be a valid analysis type
            recognized by the Spectre session.
        analysis_name : str
            The name to assign to the new analysis. This name must be unique within
            the session.

        Returns
        -------
        bool
            `True` if the analysis was successfully created, `False` if the command
            failed to execute.
        """
        pass

    @abstractmethod
    def get_circuit_parameter(self, circuit_parameter: str) -> list[tuple[str, str]]:
        """Retrieve the attributes and their values for a specified circuit parameter.

        This function sends a command to the Spectre session to list all attributes
        associated with a specified circuit parameter. It then parses the command output
        and returns a list of tuples, where each tuple contains an attribute name
        and its corresponding value.

        Parameters
        ----------
        circuit_parameter : str
            The name of the circuit parameter whose attributes and values are to be retrieved.
            This should be a valid circuit parameter name within the current Spectre session.

        Returns
        -------
        list[tuple[str, str]]
            A list of tuples where each tuple contains:
            - The name of the attribute (str).
            - The value of the attribute (str).
        """
        pass

    @abstractmethod
    def set_circuit_parameter(self, circuit_parameter: str, attribute_name: str,
                              value: str) -> bool:
        """Set the value of a specific attribute for a circuit parameter in the Spectre session.

        This function sends a command to the Spectre session to set the value of a
        specified attribute for a circuit parameter. The command is constructed based
        on the provided circuit parameter name, attribute name, and the new value.

        Parameters
        ----------
        circuit_parameter : str
            The name of the circuit parameter whose attribute is to be set. This should
            be a valid circuit parameter name within the current Spectre session.
        attribute_name : str
            The name of the attribute to be modified. This should be a valid attribute
            name for the specified circuit parameter.
        value : str
            The new value to set for the specified attribute.

        Returns
        -------
        bool
            `True` if the command to set the attribute was successfully executed,
            `False` otherwise.
        """
        pass

    @abstractmethod
    def list_instance_parameters(self, instance_name: str) -> list[tuple[str, str]]:
        """Retrieve the parameters and their values for a specified instance.

        This function sends a command to the Spectre session to list all parameters
        associated with a specific instance. It then parses the command output and
        returns a list of tuples, where each tuple contains a parameter name and its
        corresponding value.

        Parameters
        ----------
        instance_name : str
            The name of the instance whose parameters are to be retrieved. This should
            be a valid instance name within the current Spectre session.

        Returns
        -------
        list[tuple[str, str]]
            A list of tuples where each tuple contains:
            - The name of the parameter (str).
            - The value of the parameter (str).
        """
        pass

    @abstractmethod
    def get_instance_parameter(self, instance_name: str,
                               instance_parameter: str) -> list[tuple[str, str]]:
        """Retrieve the attributes and their values for a specified parameter of an instance.

        This function sends a command to the Spectre session to list all attributes
        associated with a specific parameter of a given instance. It then parses the
        command output and returns a list of tuples, where each tuple contains an
        attribute name and its corresponding value.

        Parameters
        ----------
        instance_name : str
            The name of the instance whose parameter attributes are to be retrieved.
            This should be a valid instance name within the current Spectre session.
        instance_parameter : str
            The name of the parameter whose attributes and values are to be retrieved.
            This should be a valid parameter name within the specified instance.

        Returns
        -------
        list[tuple[str, str]]
            A list of tuples where each tuple contains:
            - The name of the attribute (str).
            - The value of the attribute (str).
        """
        pass

    @abstractmethod
    def set_instance_parameter(self, instance_name: str, instance_parameter: str,
                               attribute_name: str, value: str) -> bool:
        """Set the value of a specific attribute for a parameter of an instance.

        This function sends a command to the Spectre session to set the value of a
        specified attribute for a parameter within a particular instance. The command
        is constructed based on the provided instance name, parameter name, attribute
        name, and the new value.

        Parameters
        ----------
        instance_name : str
            The name of the instance that contains the parameter to be modified. This
            should be a valid instance name within the current Spectre session.
        instance_parameter : str
            The name of the parameter whose attribute is to be set. This should be a
            valid parameter name within the specified instance.
        attribute_name : str
            The name of the attribute to be modified. This should be a valid attribute
            name for the specified parameter.
        value : str
            The new value to set for the specified attribute.

        Returns
        -------
        bool
            `True` if the command to set the attribute was successfully executed,
            `False` otherwise.
        """
        pass
