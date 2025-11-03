import itertools

from des.des import DiscreteEventSimulator
from network_simulation.link import Link
from network_simulation.network_node import NetworkNode
from network_simulation.message import Message

packet_ids = itertools.count()
flow_ids = itertools.count(1)

class Host(NetworkNode):
    def __init__(self, name: str, scheduler: DiscreteEventSimulator):
        super().__init__(name, 1, scheduler)

    def send_to(self, dst_name: str, payload: bytes, size_bytes=1500) -> None:
        assert dst_name in self.forward_table
        port_id:int = self.forward_table[dst_name]
        packet_id:int = next(packet_ids) #globally unique
        flow_id:int = next(flow_ids)

        message = Message(id=packet_id,
                            sender_id=self.name,
                            receiver_id=dst_name,
                            flow_id=flow_id,
                            five_tuple=None, #TBD implement once supporting TCP/UDP
                            size_bytes=size_bytes,
                            brith_time=self.scheduler.get_current_time(),
                            content=payload)
        self._internal_send(message, port_id)

    def on_message(self, message: Message):
        print(f"[{self.scheduler.get_current_time():.6f}s] Host {self.name} received message {message.id} from {message.sender_id} with content: {message.content}")