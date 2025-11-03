from abc import ABC
from typing import Dict, Tuple

from network_simulation.node import Node
from des.des import DiscreteEventSimulator
from network_simulation.link import Link
from network_simulation.message import Message


class NetworkNode(Node, ABC):
    def __init__(self, name: str, max_connections:int, scheduler: DiscreteEventSimulator):
        super().__init__(name, scheduler)
        self.ports_to_links: Dict[int, Link] = {}  # mapping from port identifier to link
        self.forward_table: Dict[str, int] = {}  # mapping from receiver_id to port identifier
        self.max_connections = max_connections

    #port_id starts from 1
    def connect(self, port_id:int, link:Link):
        assert port_id not in self.ports_to_links
        assert port_id <= self.max_connections
        assert self.connections_count() < self.max_connections
        self.ports_to_links[port_id] = link
        link.connect(self)

    def connections_count(self):
        return len(self.ports_to_links)

    def assert_correctly_full(self):
        assert len(self.ports_to_links) == self.max_connections
        for port in range(1, self.max_connections + 1):
            assert port in self.ports_to_links

    def set_routing(self, receiver_id:str, port_id:int):
            self.forward_table[receiver_id] = port_id

    # send a message to dst Host or Switch, via the given Link
    def _internal_send(self, message: Message, port_id: int) -> None:
        assert port_id in self.ports_to_links
        link = self.ports_to_links[port_id]
        link.transmit(message, self)
