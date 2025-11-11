from network_simulation.network_node import NetworkNode


class Switch(NetworkNode):

    def __init__(self, name: str, ports_count, scheduler, max_path:int, verbose:bool=False):
        super().__init__(name, ports_count, scheduler, max_path, verbose=verbose)

    def on_message(self, message):
        self._internal_send_ip(message)
