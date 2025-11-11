import logging
from abc import ABC
import random
from random import random as rand
from typing import Dict, List, Tuple, Set

from des.des import DiscreteEventSimulator
from network_simulation.ip import IPPrefix
from network_simulation.link import Link
from network_simulation.message import Message
from network_simulation.node import Node
from collections import defaultdict

class NetworkNode(Node, ABC):
    def __init__(self, name: str, max_connections: int, scheduler: DiscreteEventSimulator, max_path: int, verbose:bool=False):
        super().__init__(name, scheduler, verbose=verbose)
        self.ports_to_links: Dict[int, Link] = {}  # mapping from port identifier to link
        self.ip_forward_table: Dict[str, List[int]] = defaultdict(list)
        self.max_connections = max_connections
        self.port_to_messages_passed: Dict[int, Set[int]] = defaultdict(set)
        self.max_path = max_path


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
        """Register an IP prefix -> port mapping.

        If the port is attached to a link that has been marked failed, the port will be skipped
        and not added to the forwarding table (as if the route wasn't learned through this
        interface).
        """
        # If port not connected (yet) or attached link is failed, do not register
        link = self.ports_to_links.get(port_id)
        assert link is not None
        if not getattr(link, 'failed'):
            self.ip_forward_table[ip_prefix].append(port_id)


    def _internal_send_ip(self, message: Message) -> None:
        assert not message.dropped

        if message.is_expired(self.scheduler.current_time, self.max_path):
            self.handle_expired_message(message)
        elif message.lost:
           self.handle_lost_message(message)
        else: # normal message routing
            self.handle_regular_message(message)



    def handle_expired_message(self, message: Message):
        if self.verbose:
            logging.warning(f"{self.name} dropping expired message {message.id} to {message.five_tuple.dst_ip}")
        message.dropped = True


    def handle_lost_message(self, message: Message):
        relevant_ports: Set[int] = set()
        for port_id, link in self.ports_to_links.items():
            if message.id not in self.port_to_messages_passed[port_id] and not link.failed:
                relevant_ports.add(port_id)
        if relevant_ports:
            arbitrary_port_id = random.sample(relevant_ports, 1)[0]
            link = self.ports_to_links[arbitrary_port_id]
            self.port_to_messages_passed[arbitrary_port_id].add(message.id)
            if self.verbose:
                logging.debug(
                    f"{self.name} sending lost message {message.id} for destination {message.five_tuple.dst_ip} through port {arbitrary_port_id} to link {link.name}")
            link.transmit(message, self)
        else:
            if self.verbose:
                logging.warning(
                   f"{self.name} has no remaining ports to send lost message {message.id} to {message.five_tuple.dst_ip}, dropping message")
            message.dropped = True


    def handle_regular_message(self, message: Message):
        dst_ip = message.five_tuple.dst_ip

        # Find ports that match prefix to the destination IP
        relevant_ports: List[Tuple[int, int]] = []
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
            assert best_masked_ports #at least one port must exist here

            # If multiple best ports, choose one based on hash of the five-tuple for ECMP:
            # flow sticks to one path to avoid reordering
            port_index = hash(message.five_tuple) % len(best_masked_ports)
            best_port_id = best_masked_ports[port_index][0]
            if message.id in self.port_to_messages_passed[best_port_id]:
                if self.verbose:
                    logging.warning(f"message {message.id} has already been transmitted through port {best_port_id}, possible routing loop, will be treated as lost")
                message.lost = True
                self.handle_lost_message(message)
            else:
                self.port_to_messages_passed[best_port_id].add(message.id)
                link = self.ports_to_links[best_port_id]
                if self.verbose:
                    logging.debug(f"{self.name} sending for destination {dst_ip} through port {best_port_id} to link {link.name}")
                link.transmit(message, self)
        else:
            if self.verbose:
                logging.warning(f"{self.name} has no routing entry for destination IP {dst_ip}, dropping message")
            message.dropped = True

    @property
    def links(self) -> List[Link]:
        return list(self.ports_to_links.values())
