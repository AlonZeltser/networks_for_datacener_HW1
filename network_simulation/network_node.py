import logging
from abc import ABC
from typing import Dict, List, Tuple

from des.des import DiscreteEventSimulator
from network_simulation.ip import IPPrefix
from network_simulation.link import Link
from network_simulation.message import Message
from network_simulation.node import Node


class NetworkNode(Node, ABC):
    def __init__(self, name: str, max_connections: int, scheduler: DiscreteEventSimulator):
        super().__init__(name, scheduler)
        self.ports_to_links: Dict[int, Link] = {}  # mapping from port identifier to link
        self.ip_forward_table: Dict[str, List[int]] = {}
        self.max_connections = max_connections

    # port_id starts from 1
    def connect(self, port_id: int, link: Link):
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


    def set_ip_routing(self, ip_prefix: str, port_id: int):
        if ip_prefix not in self.ip_forward_table:
            self.ip_forward_table[ip_prefix] = []
        self.ip_forward_table[ip_prefix].append(port_id)

    # send a message to dst Host or Switch, via the given Link
    def _internal_send(self, message: Message, port_id: int) -> None:
        assert port_id in self.ports_to_links
        link = self.ports_to_links[port_id]
        link.transmit(message, self)

    def _internal_send_ip(self, message: Message) -> None:
        relevant_ports: List[Tuple[int, int]] = []
        dst_ip = message.five_tuple.dst_ip
        # Find ports that match prefix to the destination IP
        for prefix_str, port_ids in self.ip_forward_table.items():
            prefix = IPPrefix.from_string(prefix_str)
            if prefix.contains(dst_ip):
                for port_id in port_ids:
                    relevant_ports.append((port_id, prefix.prefix_len))
        # If any relevant ports found, apply Longest Prefix Match, since it implies shortest path
        if relevant_ports:
            # Longest Prefix Match: choose the port with the longest matching prefix
            relevant_ports.sort(key=lambda x: x[1], reverse=True)
            longest_mask_len = relevant_ports[0][1]
            best_masked_ports = [p for p in relevant_ports if p[1] == longest_mask_len]
            # If multiple best ports, choose one based on hash of the five-tuple for ECMP:
            # flow sticks to one path to avoid reordering
            if best_masked_ports:
                port_index = hash(message.five_tuple) % len(best_masked_ports)
                best_port_id = best_masked_ports[port_index][0]
                assert best_port_id in self.ports_to_links
                link = self.ports_to_links[best_port_id]
                logging.debug(f"{self.name} sending for destination {dst_ip} through port {best_port_id} to link {link.name}")
                link.transmit(message, self)
        else:
            raise ValueError(f"No IP routing entry for destination IP {dst_ip} in node {self.name}")

