
from network_simulation.network_node import NetworkNode
from network_simulation.link import Link
from typing import Dict, Tuple

class Switch(NetworkNode):

    def __init__(self, name: str, scheduler):
        super().__init__(name, scheduler)


    def on_message(self, message):
        if message.receiver_id not in self.forward_table:
            print(f"[{self.scheduler.get_current_time():.6f}s] Switch {self.name} has no routing entry for receiver {message.receiver_id}. Packet Dropped.")
            return
        port_id:int = self.forward_table[message.receiver_id]
        if port_id not in self.ports_to_links:
            print(f"[{self.scheduler.get_current_time():.6f}s] Switch {self.name} has no port {port_id}. Packet dropped.")
            return
        self._internal_send(message, port_id)
