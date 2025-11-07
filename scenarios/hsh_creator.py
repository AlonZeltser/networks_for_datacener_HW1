from network_simulation.simulator_creator import SimulatorCreator


class HSHCreator(SimulatorCreator):
    def __init__(self, **viz_options):
        super().__init__(**viz_options)

    def create_topology(self):
        h1 = self.create_host('Host1')
        h2 = self.create_host('Host2')
        s1 = self.create_switch('Switch1', 2)

        l1 = self.create_link("h1_s1", 1e3, 0.01)
        l2 = self.create_link('h2_s1', 1e5, 0.01)

        # physical connection of h1 <-> l1 <-> s1 <-> l2 <-> h2
        h1.connect(1, l1)
        h2.connect(1, l2)
        s1.connect(1, l1)
        s1.connect(2, l2)

        # routing table entries of each host / switch
        h1.set_routing('Host2', 1)
        h2.set_routing('Host1', 1)
        s1.set_routing('Host2', 2)
        s1.set_routing('Host1', 1)

    def create_scenario(self):
        def e1():
            h1 = self.get_entity('Host1')
            h1.send_to('Host2', 'Hello, Host2!', size_bytes=500000)
            h1.send_to('Host2', 'Hellow again, Host2!', size_bytes=500000)

        def e2():
            h2 = self.get_entity('Host2')
            h2.send_to('Host1', 'bye bye, Host1!', size_bytes=100)

        def e3():
            h1 = self.get_entity('Host1')
            h1.send_to('Host2', 'see you, Host2!', size_bytes=50)
            h2 = self.get_entity('Host2')
            h2.send_to('Host1', 'here again, Host1!', size_bytes=10000)

        for i in range(0, 1000):
            self.simulator.schedule_event(i / 10.0, e1)
            self.simulator.schedule_event(i, e2)
        for i in range(0, 2000):
            self.simulator.schedule_event(i / 10.0, e1)
            self.simulator.schedule_event(i, e2)
