from abc import ABC, abstractmethod
from typing import Any, Optional, Tuple

from des.des import DiscreteEventSimulator
from network_simulation.host import Host
from network_simulation.link import Link
from network_simulation.switch import Switch
from network_simulation.visualizer import visualize_topology
from network_simulation.ip import IPAddress


class SimulatorCreator(ABC):
    def __init__(self, *, visualize: bool = False,
                 visualize_show: bool = True, visualize_save: bool = True,
                 visualize_save_path: Optional[str] = None,
                 visualize_figsize: Optional[Tuple[float, float]] = None,
                 visualize_spacing: float = 2.0):
        """Base class for topology/scenario creators.

        Parameters:
        - visualize: whether to produce a visualization
        - visualize_show: if True, attempt to show the visualization window
        - visualize_save: if True, save the visualization to a file
        - visualize_save_path: optional path to save the visualization (PNG). If None a timestamped file is used.
        - visualize_figsize: optional (width, height) in inches to override automatic sizing
        - visualize_spacing: multiplier controlling how far apart nodes are placed horizontally (default 2.0)
        """
        self.simulator = DiscreteEventSimulator()
        self.entities = {}
        self._visualize = visualize
        self._visualize_show = visualize_show
        self._visualize_save = visualize_save
        self._visualize_save_path = visualize_save_path
        # New visualization tuning options
        self._visualize_figsize = visualize_figsize
        self._visualize_spacing = max(0.1, float(visualize_spacing))

    def create_simulator(self) -> DiscreteEventSimulator:
        # Build topology
        self.create_topology()

        # Build scenario (traffic, flows, etc.)
        self.create_scenario()

        # Optionally visualize after scenario creation
        if self._visualize:
            visualize_topology("fat_tree_simulator", self.entities, show=self._visualize_show,
                               save=self._visualize_save,
                               path=self._visualize_save_path, spacing=self._visualize_spacing,
                               figsize=self._visualize_figsize)

        return self.simulator

    def create_host(self, name: str, ip_address: Optional[IPAddress] = None) -> Host:
        h = Host(name, self.simulator)
        self.entities[name] = h
        return h

    def create_switch(self, name: str, ports_count: int) -> Switch:
        """Create a switch with the given number of ports."""
        s = Switch(name, ports_count, self.simulator)
        self.entities[name] = s
        return s

    def create_link(self, name: str, bandwidth: float, delay: float) -> Link:
        l = Link(name, self.simulator, bandwidth, delay)
        self.entities[name] = l
        return l

    def get_entity(self, name: str) -> Any:
        return self.entities.get(name)

    @abstractmethod
    def create_topology(self):
        pass

    @abstractmethod
    def create_scenario(self):
        pass
