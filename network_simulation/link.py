from typing import Optional

from des.des import DiscreteEventSimulator
from network_simulation.message import Message
from network_simulation.node import Node


class Link:
    def __init__(self, name: str, scheduler: DiscreteEventSimulator, bandwidth_bps: float,
                 propagation_time: float):
        self.name = name
        self.scheduler = scheduler
        self.bandwidth_bps = bandwidth_bps
        self.propagation_time = propagation_time
        self.next_available_time = [0.0, 0.0]  # in seconds, full duplex link
        self.node1: Optional[Node] = None
        self.node2: Optional[Node] = None
        # whether this link is failed (physically down). Default: False
        self.failed: bool = False

        #for statistics
        self.accumulated_transmitting_time: float = 0.0
        self.accumulated_bytes_transmitted: int = 0

    def connect(self, node: Node) -> None:
        if self.node1 is None:
            self.node1 = node
        elif self.node2 is None:
            self.node2 = node
        else:
            raise Exception("Link can only connect two nodes")

    def transmit(self, message: Message, sender: Node) -> None:
        assert self.node1 is not None and self.node2 is not None and (sender == self.node1 or sender == self.node2)
        assert not self.failed
        dst = self.node2 if sender == self.node1 else self.node1
        link_index = 0 if sender == self.node1 else 1
        now = self.scheduler.get_current_time()
        actual_start_time = max(now, self.next_available_time[link_index])
        serialization_duration = message.size_bytes * 8 / self.bandwidth_bps  # in seconds
        self.accumulated_transmitting_time += serialization_duration
        self.accumulated_bytes_transmitted += message.size_bytes
        finish_serialization_time = actual_start_time + serialization_duration
        self.next_available_time[link_index] = finish_serialization_time
        arrival_time = finish_serialization_time + self.propagation_time

        def deliver():
            dst.post(message)

        # at arrival nominal time, the message will be posted on the destination Host / Switch
        self.scheduler.schedule_event(arrival_time - now, deliver)
