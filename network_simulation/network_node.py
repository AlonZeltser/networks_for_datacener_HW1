from abc import ABC
from typing import Dict, Tuple

from network_simulation.node import Node
from des.des import DiscreteEventSimulator
from network_simulation.link import Link
from network_simulation.message import Message


class NetworkNode(Node, ABC):
    def __init__(self, name: str, scheduler: DiscreteEventSimulator):
        super().__init__(name, scheduler)
        self.ports_to_links: Dict[int, Link] = {}  # mapping from port identifier to link
        self.forward_table: Dict[str, int] = {}  # mapping from receiver_id to port identifier

    def connect(self, port_id:int, link:Link):
        self.ports_to_links[port_id] = link
        link.connect(self)

    def set_routing(self, receiver_id:str, port_id:int):
            self.forward_table[receiver_id] = port_id

    # send a message to dst Host or Switch, via the given Link
    def _internal_send(self, message: Message, port_id: int) -> None:
        assert port_id in self.ports_to_links
        link = self.ports_to_links[port_id]
        link.transmit(message, self)
