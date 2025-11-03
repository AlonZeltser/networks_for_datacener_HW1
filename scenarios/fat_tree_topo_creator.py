from scenarios.simulator_creator import SimulatorCreator


class FatTreeTopoCreator(SimulatorCreator):

    def __init__(self, k):
        super().__init__()
        assert k >= 1
        assert k % 2 == 0
        self.k = k  # Number of ports per switch

    def create_topology(self):
        bandwidth = 1e9
        pods_count = self.k
        core_switches_count = (self.k // 2) ** 2
        agg_switches_per_pod = self.k // 2
        total_agg_switches = pods_count * agg_switches_per_pod
        edge_switches_per_pod = self.k // 2
        total_edge_switches = pods_count * edge_switches_per_pod
        hosts_per_edge_switch = self.k // 2
        total_hosts = total_edge_switches * hosts_per_edge_switch


        for pod in range(pods_count):
            for edge in range(edge_switches_per_pod):
                edge_switch_name = f'edge_switch_p{pod}_e{edge}'
                s = self.create_switch(edge_switch_name, self.k)
                for host in range(hosts_per_edge_switch):
                    host_name = f'host_p{pod}_e{edge}_h{host}'
                    h = self.create_host(host_name)
                    link_name = f'link_{host_name}_{edge_switch_name}'
                    l = self.create_link(link_name, bandwidth=bandwidth, delay=0.01)
                    h.connect(1, l)
                    s.connect(1 + host, l)
            for agg in range(agg_switches_per_pod):
                agg_switch_name = f'agg_switch_p{pod}_a{agg}'
                s_agg = self.create_switch(agg_switch_name, self.k)
                edge_switch_start_port = 1 + hosts_per_edge_switch
                for edge in range(edge_switches_per_pod):
                    edge_switch_name = f'edge_switch_p{pod}_e{edge}'
                    l = self.create_link(f'link_{agg_switch_name}_{edge_switch_name}', bandwidth=bandwidth, delay=0.01)
                    s_agg.connect(1 + edge, l)
                    edge_switch = self.get_entity(edge_switch_name)
                    edge_switch.connect(edge_switch_start_port + agg, l)

            for edge in range(edge_switches_per_pod):
                edge_switch_name = f'edge_switch_p{pod}_e{edge}'
                s_edge = self.get_entity(edge_switch_name)
                s_edge.assert_correctly_full()

        for core in range(core_switches_count):
            core_switch_name = f'core_switch_c{core}'
            s_core = self.create_switch(core_switch_name, self.k)
            aggregation_start_port = 1 + edge_switches_per_pod
            port_in_aggregation = aggregation_start_port + core % (self.k//2)
            aggregation_switch_in_pod = core // (self.k // 2)
            for pod in range(pods_count):
                agg_switch_name = f'agg_switch_p{pod}_a{aggregation_switch_in_pod}'
                l = self.create_link(f'link_c{core_switch_name}_e{agg_switch_name}', bandwidth=bandwidth, delay=0.01)
                s_core.connect(1 + pod, l)
                agg_switch = self.get_entity(agg_switch_name)
                agg_switch.connect(port_in_aggregation, l)
        for core in range(core_switches_count):
            core_switch_name = f'core_switch_c{core}'
            s_core = self.get_entity(core_switch_name)
            s_core.assert_correctly_full()
        for pod in range(pods_count):
            for agg in range(agg_switches_per_pod):
                agg_switch_name = f'agg_switch_p{pod}_a{agg}'
                s_agg = self.get_entity(agg_switch_name)
                s_agg.assert_correctly_full()


        # print counts per layer and servers
        print(f"Fat-tree (k={self.k}) topology summary:")
        print(f"  Core switches: {core_switches_count}")
        print(f"  Aggregation switches: {total_agg_switches} ({agg_switches_per_pod} per pod)")
        print(f"  Edge switches: {total_edge_switches} ({edge_switches_per_pod} per pod)")
        print(f"  Servers (hosts): {total_hosts} ({hosts_per_edge_switch} per edge switch)")

    def create_scenario(self):
        pass