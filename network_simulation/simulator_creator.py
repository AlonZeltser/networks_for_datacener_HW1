from abc import ABC, abstractmethod
from typing import Any, Dict, List

import random
import logging

from des.des import DiscreteEventSimulator
from network_simulation.host import Host
from network_simulation.link import Link
from network_simulation.switch import Switch
from network_simulation.visualizer import visualize_topology


class SimulatorCreator(ABC):
    def __init__(self, name:str, max_path: int, visualize: bool = False,
                 link_failure_percent: float = 0.0 ):
        """Base class for topology/scenario creators.

        Parameters:
        name: name of the topology/scenario
        visualize: whether to produce a visualization
        link_failure_percent: percentage (0-100) of links to mark as failed at creation time
        """
        self.simulator = DiscreteEventSimulator()
        self.entities: Dict[str, Any] = {}
        self.hosts: Dict[str, Host] = {}
        self._visualize = visualize
        # visualization options (may be provided via viz_options)
        self.name = name
        # keep track of links for potential reporting
        self._links: List[Link] = []
        # store percent as a 0..100 float
        self.link_failure_percent = float(link_failure_percent)
        self.max_path = max_path

    def create_simulator(self) -> DiscreteEventSimulator:
        # Build topology
        self.create_topology()

        # After topology created, log a short summary of failed links (if any)
        if self.link_failure_percent and self.link_failure_percent > 0.0:
            failed = [l.name for l in self._links if getattr(l, 'failed', False)]
            if failed:
                logging.info(f"Link failure summary: {len(failed)} links marked as failed: {failed}")
            else:
                logging.info("Link failure summary: 0 links marked as failed")

        # Build scenario (traffic, flows, etc.)
        self.create_scenario()

        # Optionally visualize after scenario creation
        if self._visualize:
            visualize_topology(
                self.name,
                self.entities)

        return self.simulator

    def create_host(self, name: str, ip_address: str) -> Host:
        h = Host(name, self.simulator, ip_address, self.max_path)
        assert name not in self.entities and name not in self.hosts
        self.entities[name] = h
        self.hosts[name] = h
        return h

    def create_switch(self, name: str, ports_count: int) -> Switch:
        """Create a switch with the given number of ports."""
        s = Switch(name, ports_count, self.simulator, self.max_path)
        assert name not in self.entities
        self.entities[name] = s
        return s

    def create_link(self, name: str, bandwidth: float = 1e6, delay: float = 1e-3) -> Link:
        l = Link(name, self.simulator, bandwidth, delay)
        assert name not in self.entities
        self.entities[name] = l
        # decide at creation time whether this link is a failed one according to the configured percentage
        if self.link_failure_percent and self.link_failure_percent > 0.0:
            # probability p = link_failure_percent / 100.0
            p = max(0.0, min(100.0, self.link_failure_percent)) / 100.0
            l.failed = random.random() < p
        else:
            l.failed = False
        # track created links for reporting
        self._links.append(l)
        return l

    def get_entity(self, name: str) -> Any:
        return self.entities.get(name)

    @abstractmethod
    def create_topology(self):
        pass

    @abstractmethod
    def create_scenario(self):
        pass

    @property
    def links(self):
        return self._links
