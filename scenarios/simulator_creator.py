from abc import ABC, abstractmethod
from typing import Any

from des.des import DiscreteEventSimulator
from network_simulation.host import Host
from network_simulation.link import Link
from network_simulation.switch import Switch

class SimulatorCreator(ABC):
    def __init__(self):
        self.simulator = DiscreteEventSimulator()
        self.entities = {}

    def create_simulator(self) -> DiscreteEventSimulator:
        self.create_topology()
        self.create_scenario()
        return self.simulator

    def create_host(self, name:str) -> Host:
        h = Host(name, self.simulator)
        self.entities[name] = h
        return h
    def create_switch(self, name:str) -> Switch:
        s = Switch(name, self.simulator)
        self.entities[name] = s
        return s
    def create_link(self, name:str, bandwidth:float, delay:float) -> Link:
        l = Link(name, self.simulator, bandwidth, delay)
        self.entities[name] = l
        return l
    def get_entity(self, name:str) -> Any:
        return self.entities.get(name)

    @abstractmethod
    def create_topology(self):
        pass

    @abstractmethod
    def create_scenario(self):
        pass
