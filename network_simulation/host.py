import itertools
import logging
import re
from typing import Optional

from des.des import DiscreteEventSimulator
from network_simulation.ip import IPAddress
from network_simulation.message import Message, FiveTuple, Protocol
from network_simulation.network_node import NetworkNode

packet_ids = itertools.count()
flow_ids = itertools.count(1)


class Host(NetworkNode):
    def __init__(self, name: str, scheduler: DiscreteEventSimulator, ip_address: str, max_path: int, verbose:bool=False):
        super().__init__(name, 1, scheduler, max_path, verbose=verbose)
        self._ip_address: str = ip_address
        self._received_count: int = 0

    @property
    def ip_address(self) -> str:
        return self._ip_address

    def send_to_ip(self, dst_ip_address: str, payload: bytes, size_bytes=1500) -> None:
        packet_id: int = next(packet_ids)  # globally unique

        message = Message(id=packet_id,
                          sender_id="",
                          five_tuple= FiveTuple(self.ip_address, dst_ip_address, 0, 0, Protocol.TCP),
                          size_bytes=size_bytes,
                          brith_time=self.scheduler.get_current_time(),
                          content=payload,
                          ttl=2000)
        message.path_length += 1
        if self.verbose:
            message.verbose_path.append(self.name)
        self.scheduler.messages.append(message)
        self._internal_send_ip(message)

    def on_message(self, message: Message):
        message.delivered = True
        message.arrival_time = self.scheduler.get_current_time()
        self._received_count += 1
        if self.verbose:
            logging.debug(f"Received message: {message}"
                f"[{self.scheduler.get_current_time():.6f}s] Host {self.name} received message {message.id} from {message.sender_id} with content: {message.content}")

    @property
    def received_count(self) -> int:
        return self._received_count
