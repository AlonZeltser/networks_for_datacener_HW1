import itertools
import re
from typing import Optional

from des.des import DiscreteEventSimulator
from network_simulation.ip import IPAddress
from network_simulation.message import Message
from network_simulation.network_node import NetworkNode

packet_ids = itertools.count()
flow_ids = itertools.count(1)


class Host(NetworkNode):
    def __init__(self, name: str, scheduler: DiscreteEventSimulator, ip_address: Optional[IPAddress] = None):
        super().__init__(name, 1, scheduler)

        # Assign IP according to Fat-Tree scheme (Al-Fares style): 10.<pod>.<edge>.<host>
        # Assumption: pods/edge/host indices in names start at 0 in this codebase, so add +1
        # to move to more conventional non-zero octets: 10.(pod+1).(edge+1).(host+1)
        # Host names follow the pattern: 'host_p{pod}_e{edge}_h{host}'
        self._ip_address = ip_address
        if self.ip_address is None:
            m = re.match(r"host_p(\d+)_e(\d+)_h(\d+)$", name)
            if m:
                pod_idx = int(m.group(1))
                edge_idx = int(m.group(2))
                host_idx = int(m.group(3))
                # apply +1 offset so octets are in range 1..255 (avoid 0)
                octets = (10, pod_idx + 1, edge_idx + 1, host_idx + 1)
                self._ip_address = IPAddress.parse(octets)
            else:
                raise ValueError(
                    f"Cannot assign IP address to host with name '{name}'. Provide an explicit IP address.")

    @property
    def ip_address(self) -> Optional[IPAddress]:
        """Return the host IPAddress (or None if not assigned).

        Note: IPs are assigned only for hosts named 'host_p{pod}_e{edge}_h{host}'.
        """
        return self._ip_address

    def send_to(self, dst_name: str, payload: bytes, size_bytes=1500) -> None:
        assert dst_name in self.forward_table
        port_id: int = self.forward_table[dst_name]
        packet_id: int = next(packet_ids)  # globally unique
        flow_id: int = next(flow_ids)

        message = Message(id=packet_id,
                          sender_id=self.name,
                          receiver_id=dst_name,
                          flow_id=flow_id,
                          five_tuple=None,  # TBD implement once supporting TCP/UDP
                          size_bytes=size_bytes,
                          brith_time=self.scheduler.get_current_time(),
                          content=payload)
        self._internal_send(message, port_id)

    def on_message(self, message: Message):
        print(
            f"[{self.scheduler.get_current_time():.6f}s] Host {self.name} received message {message.id} from {message.sender_id} with content: {message.content}")
