import functools
import logging

from network_simulation.host import Host
from network_simulation.simulator_creator import SimulatorCreator
import random

from network_simulation.switch import Switch


class FatTreeTopoCreator(SimulatorCreator):

    def __init__(self, k:int, visualize:bool, max_path:int, link_failure_percent:float=0.0):
        super().__init__("fat tree", max_path, visualize, link_failure_percent=link_failure_percent)
        assert k >= 1
        assert k % 2 == 0
        self.k = k  # Number of ports per switch

    def create_topology(self):
        bandwidth = 1e9
        delay = 0.0001 # 100us
        pods_count = self.k
        core_switches_count = (self.k // 2) ** 2
        agg_switches_per_pod = self.k // 2
        total_agg_switches = pods_count * agg_switches_per_pod
        edge_switches_per_pod = self.k // 2
        total_edge_switches = pods_count * edge_switches_per_pod
        hosts_per_edge_switch = self.k // 2
        total_hosts = total_edge_switches * hosts_per_edge_switch


        for pod_index in range(pods_count):
            # creat pod: edge switches, agg switches, hosts
            for edge_index in range(edge_switches_per_pod):
                #create edge-switch and its hosts
                edge_switch_name = f'edge_switch_p{pod_index}_e{edge_index}'
                switch = self.create_switch(edge_switch_name, self.k)
                for host_index in range(hosts_per_edge_switch):
                    #create host, link to edge switch and set routing
                    host_name = f'host_p{pod_index}_e{edge_index}_h{host_index}'
                    host = self.create_host(host_name, f"10.{pod_index + 1}.{edge_index + 1}.{host_index + 1}")
                    link_name = f'link_{host_name}_{edge_switch_name}'
                    link = self.create_link(link_name, bandwidth=bandwidth, delay=delay)
                    edge_to_host_port = 1 + host_index
                    host.connect(1, link)
                    switch.connect(edge_to_host_port, link)
                    host.set_ip_routing("10.0.0.0/8", 1)  # default route to edge switch
                    switch.set_ip_routing(host.ip_address+f"/32", edge_to_host_port)  # route to host via its port
            for aggregation_index in range(agg_switches_per_pod):
                # create an aggregation switch, the link to each edge switch in the pod and set routing
                agg_switch_name = f'agg_switch_p{pod_index}_a{aggregation_index}'
                agg_switch = self.create_switch(agg_switch_name, self.k)
                edge_switch_start_port = 1 + hosts_per_edge_switch
                for edge_index in range(edge_switches_per_pod):
                    # create link between agg switch and edge switch, and set routing
                    edge_switch_name = f'edge_switch_p{pod_index}_e{edge_index}'
                    link = self.create_link(f'link_{agg_switch_name}_{edge_switch_name}', bandwidth=bandwidth, delay=delay)
                    agg_to_edge_port = edge_index + 1
                    agg_switch.connect(agg_to_edge_port, link)
                    agg_switch.set_ip_routing(f"10.{pod_index + 1}.{edge_index + 1}.0/24", agg_to_edge_port)  #
                    edge_switch = self.get_entity(edge_switch_name)
                    edge_to_agg_port = edge_switch_start_port + aggregation_index
                    edge_switch.connect(edge_to_agg_port, link)
                    # instead of specifying all hosts in pod which are not in this edge + all other pods,
                    # we can use a broader route that will have less priority if the dest
                    #is within this edge switch's hosts
                    edge_switch.set_ip_routing(f"10.0.0.0/8", edge_to_agg_port)

            for edge_index in range(edge_switches_per_pod):
                edge_switch_name = f'edge_switch_p{pod_index}_e{edge_index}'
                edge_switch = self.get_entity(edge_switch_name)
                edge_switch.assert_correctly_full()

        for core_index in range(core_switches_count):
            #set core switch, links to aggregation switches and routing
            core_switch_name = f'core_switch_c{core_index}'
            core_switch = self.create_switch(core_switch_name, self.k)
            #each core switch connects to a one certain aggregation switch in each pod (same for all pods)
            aggregation_switch_in_pod = core_index // (self.k // 2)
            aggregation_start_port = edge_switches_per_pod + 1
            port_in_aggregation = aggregation_start_port + core_index % (self.k // 2)
            for pod_index in range(pods_count):
                #get the aggregation switch in this pod
                agg_switch_name = f'agg_switch_p{pod_index}_a{aggregation_switch_in_pod}'
                agg_switch = self.get_entity(agg_switch_name)
                link = self.create_link(f'link_c{core_switch_name}_e{agg_switch_name}', bandwidth=bandwidth, delay=delay)
                port_in_core = pod_index + 1
                core_switch.connect(port_in_core, link)
                core_switch.set_ip_routing(f"10.{pod_index + 1}.0.0/16", port_in_core)  #
                agg_switch.connect(port_in_aggregation, link)
                agg_switch.set_ip_routing(f"10.0.0.0/8", port_in_aggregation)
        for core_index in range(core_switches_count):
            core_switch_name = f'core_switch_c{core_index}'
            core_switch = self.get_entity(core_switch_name)
            core_switch.assert_correctly_full()
        for pod_index in range(pods_count):
            for aggregation_index in range(agg_switches_per_pod):
                agg_switch_name = f'agg_switch_p{pod_index}_a{aggregation_index}'
                agg_switch = self.get_entity(agg_switch_name)
                agg_switch.assert_correctly_full()

        # print counts per layer and servers
        print(f"Fat-tree (k={self.k}) topology summary:")
        print(f"  Core switches: {core_switches_count}")
        print(f"  Aggregation switches: {total_agg_switches} ({agg_switches_per_pod} per pod)")
        print(f"  Edge switches: {total_edge_switches} ({edge_switches_per_pod} per pod)")
        print(f"  Servers (hosts): {total_hosts} ({hosts_per_edge_switch} per edge switch)")
        self.log_all_routing_tables()

    def log_all_routing_tables(self):
        for entity in self.entities.values():
            if isinstance(entity, Host) or isinstance(entity, Switch):
                logging.info(f"Routing table for {entity.name}: {entity.ip_forward_table}")

    def create_scenario(self):
        for host in self.hosts.values():
            #self.host_calls_itself(host)
            #self.host_calls_random_host(host)
            self.loadded_calls(host)

    def host_calls_itself(self, host):
        # Example traffic scenario: each host sends a message to itself after a delay
        send_time = random.uniform(0.1, 10)  # send between 0.1s and 1.0s
        def send_message_to_self(source:Host):
            source.send_to_ip(source.ip_address,f'Self-message from {source.name}', size_bytes=500)
        logging.info(f"Creating self-traffic scenario for {host.name}")
        self.simulator.schedule_event(send_time, functools.partial(send_message_to_self, host))

    def host_calls_random_host(self, host):
        # Example traffic scenario: each host sends a message to a random other host after a delay
        all_other_host_names = [name for name in self.hosts.keys() if name != host.name]
        if not all_other_host_names:
            return
        dst_host_name = random.choice(all_other_host_names)
        logging.info(f"Creating random host traffic from {host.name} to {dst_host_name}")
        dst_host = self.get_entity(dst_host_name)
        assert dst_host is not None
        send_time = random.uniform(0.1, 10)  # send between 0.1s and 10.0s
        def send_message(source:Host, dst_host:Host):
            source.send_to_ip(dst_host.ip_address,f'Message from {source.name} to {dst_host.name}', size_bytes=1000)
        self.simulator.schedule_event(send_time, functools.partial(send_message, host, dst_host))

    def loadded_calls(self, host):
        # Example traffic scenario: each host sends messages to a random other host

        all_other_host_names = [name for name in self.hosts.keys() if name != host.name]
        if not all_other_host_names:
            return
        num_messages = 10
        message_size_bytes = int(1e10/8) #10Gb
        time_interval_between_messages = 0
        send_time = 0.0
        for _ in range(num_messages):
            dst_host_name = random.choice(all_other_host_names)
            logging.debug(f"Creating host traffic from {host.name} to {dst_host_name}")
            dst_host = self.get_entity(dst_host_name)
            assert dst_host is not None
            send_time = random.uniform(0.1, 10.0)  # send between 0.1s and 1.0s
            def send_message(source:Host, dst_host:Host):
                source.send_to_ip(dst_host.ip_address,f'Message from {source.name} to {dst_host.name}', size_bytes=message_size_bytes)
            self.simulator.schedule_event(send_time, functools.partial(send_message, host, dst_host))
            send_time += time_interval_between_messages
