from abc import ABC, abstractmethod
from typing import Any, Optional
import datetime
import os

from des.des import DiscreteEventSimulator
from network_simulation.host import Host
from network_simulation.link import Link
from network_simulation.switch import Switch


class SimulatorCreator(ABC):
    def __init__(self, *, visualize: bool = False, visualize_before_run: bool = False,
                 visualize_show: bool = True, visualize_save: bool = True,
                 visualize_save_path: Optional[str] = None):
        """Base class for topology/scenario creators.

        Parameters:
        - visualize: whether to produce a visualization
        - visualize_before_run: if True, visualize after topology creation and before scenario/run
        - visualize_show: if True, attempt to show the visualization window
        - visualize_save: if True, save the visualization to a file
        - visualize_save_path: optional path to save the visualization (PNG). If None a timestamped file is used.
        """
        self.simulator = DiscreteEventSimulator()
        self.entities = {}
        self._visualize = visualize
        self._visualize_before_run = visualize_before_run
        self._visualize_show = visualize_show
        self._visualize_save = visualize_save
        self._visualize_save_path = visualize_save_path

    def create_simulator(self) -> DiscreteEventSimulator:
        # Build topology
        self.create_topology()
        # Optionally visualize after topology creation (before scenario or run)
        if self._visualize and self._visualize_before_run:
            self.visualize_topology(show=self._visualize_show, save=self._visualize_save, path=self._visualize_save_path)

        # Build scenario (traffic, flows, etc.)
        self.create_scenario()

        # Optionally visualize after scenario creation
        if self._visualize and not self._visualize_before_run:
            self.visualize_topology(show=self._visualize_show, save=self._visualize_save, path=self._visualize_save_path)

        return self.simulator

    def create_host(self, name: str) -> Host:
        h = Host(name, self.simulator)
        self.entities[name] = h
        return h

    def create_switch(self, name: str, ports_count: int) -> Switch:
        """Create a switch with the given number of ports."""
        s = Switch(name, ports_count, self.simulator)
        self.entities[name] = s
        return s

    def create_link(self, name: str, bandwidth: float, delay: float) -> Link:
        l = Link(name, self.simulator, bandwidth, delay)
        self.entities[name] = l
        return l

    def get_entity(self, name: str) -> Any:
        return self.entities.get(name)

    def visualize_topology(self, show: bool = True, save: bool = True, path: Optional[str] = None) -> Optional[str]:
        """Create a visualization of the topology using networkx + matplotlib if available.

        Returns the path to the saved file if saved, otherwise None.
        """
        # Lazy import so visualization is optional
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except Exception:
            print("Visualization requires 'networkx' and 'matplotlib'. Install them to enable topology plots.")
            return None

        # Build graph
        G = nx.Graph()
        node_types = {}
        # Add node vertices for non-link entities
        for name, ent in self.entities.items():
            if ent is None:
                continue
            cls_name = ent.__class__.__name__.lower()
            if cls_name.startswith("host"):
                node_types[name] = "host"
                G.add_node(name)
            elif cls_name.startswith("switch"):
                node_types[name] = "switch"
                G.add_node(name)

        # Add edges from Link objects (they hold node1/node2 references)
        for name, ent in self.entities.items():
            if ent is None:
                continue
            if hasattr(ent, "node1") and hasattr(ent, "node2"):
                n1 = getattr(ent.node1, "name", None)
                n2 = getattr(ent.node2, "name", None)
                if n1 and n2:
                    G.add_edge(n1, n2, label=name)

        if G.number_of_nodes() == 0:
            print("No nodes to visualize in the topology.")
            return None

        # Prefer a layered tree-like layout (core -> aggregation -> edge -> hosts) when node naming follows
        # the fat-tree conventions. Otherwise fall back to graphviz or spring layout.
        try:
            # classify nodes by name prefixes commonly used in fat-tree creator
            cores = sorted([n for n in G.nodes() if str(n).startswith('core_switch')])
            aggs = sorted([n for n in G.nodes() if str(n).startswith('agg_switch')])
            edges = sorted([n for n in G.nodes() if str(n).startswith('edge_switch')])
            hosts = sorted([n for n in G.nodes() if str(n).startswith('host')])

            layers = [cores, aggs, edges, hosts]
            # keep only non-empty layers, but preserve order
            layers = [layer for layer in layers if layer]

            if len(layers) >= 2:
                pos = {}
                top = 1.0
                bottom = 0.0
                step = (top - bottom) / (len(layers) - 1) if len(layers) > 1 else 0
                for i, layer in enumerate(layers):
                    y = top - i * step
                    m = len(layer)
                    if m == 1:
                        xs = [0.5]
                    else:
                        xs = [j / (m - 1) for j in range(m)]
                    for node, x in zip(layer, xs):
                        pos[node] = (x, y)

                # Place any leftover nodes (not matched by prefixes) in the middle row(s)
                leftover = [n for n in G.nodes() if n not in pos]
                if leftover:
                    mid_y = (top + bottom) / 2
                    m = len(leftover)
                    xs = [j / (m - 1) if m > 1 else 0.5 for j in range(m)]
                    for node, x in zip(leftover, xs):
                        pos[node] = (x, mid_y)
            else:
                # Fallback to graphviz or spring layout
                try:
                    pos = nx.nx_pydot.graphviz_layout(G, prog="dot")
                except Exception:
                    pos = nx.spring_layout(G, seed=42)
        except Exception:
            # In case anything unexpected happens, fallback to spring layout
            try:
                pos = nx.nx_pydot.graphviz_layout(G, prog="dot")
            except Exception:
                pos = nx.spring_layout(G, seed=42)

        # Node styling
        colors = []
        sizes = []
        for n in G.nodes():
            t = node_types.get(n, "switch")
            if t == "host":
                colors.append("lightblue")
                sizes.append(150)
            else:
                colors.append("orange")
                sizes.append(600)

        plt.figure(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, node_color=colors, node_size=sizes, font_size=8)
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)

        saved_path = None
        if save:
            if path is None:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"topology_{self.__class__.__name__}_{timestamp}.png"
            plt.savefig(path, bbox_inches='tight')
            saved_path = path
            print(f"Topology saved to {path}")
            # try opening automatically on Windows
            try:
                if os.name == 'nt':
                    os.startfile(path)
            except Exception:
                pass

        if show:
            try:
                plt.show()
            except Exception:
                # If show fails (headless), just continue
                pass
        plt.close()
        return saved_path

    @abstractmethod
    def create_topology(self):
        pass

    @abstractmethod
    def create_scenario(self):
        pass
