import datetime
import os
from typing import Optional, Dict, Any, Tuple


def visualize_topology(name: str, entities: Dict[Any, Any], show: bool = True, save: bool = True,
                       path: Optional[str] = None, spacing: float = 2.0,
                       figsize: Optional[Tuple[float, float]] = None) -> Optional[str]:
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
    for name, ent in entities.items():
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
    for name, ent in entities.items():
        if ent is None:
            continue
        if hasattr(ent, "node1") and hasattr(ent, "node2"):
            n1 = getattr(ent.node1, "name", None)
            n2 = getattr(ent.node2, "name", None)
            if n1 and n2:
                # Use simple edge label (link name). Port annotations removed for readability.
                G.add_edge(n1, n2, label=name)

    if G.number_of_nodes() == 0:
        print("No nodes to visualize in the topology.")
        return None

    # Prefer a layered tree-like layout (core -> aggregation -> edge -> hosts) when node naming follows
    # the fat-tree conventions. Otherwise fall back to graphviz or spring layout.
    layers = []  # initialize so it's available for sizing even if classification fails
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
                    # spread nodes horizontally with a center and a step that depends on spacing
                    center = (m - 1) / 2.0
                    step_x = spacing / max(1, (m - 1))
                    xs = [0.5 + (j - center) * step_x for j in range(m)]
                for node, x in zip(layer, xs):
                    pos[node] = (x, y)

            # Place any leftover nodes (not matched by prefixes) in the middle row(s)
            leftover = [n for n in G.nodes() if n not in pos]
            if leftover:
                mid_y = (top + bottom) / 2
                m = len(leftover)
                if m == 1:
                    xs = [0.5]
                else:
                    center = (m - 1) / 2.0
                    step_x = spacing / max(1, (m - 1))
                    xs = [0.5 + (j - center) * step_x for j in range(m)]
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

    # Ensure layers has a usable default for sizing if classification failed
    if not layers:
        layers = [list(G.nodes())]

    # Node styling
    colors = []
    sizes = []
    for n in G.nodes():
        t = node_types.get(n, "switch")
        if t == "host":
            colors.append("lightblue")
            # make hosts slightly larger and scale with spacing so labels are more visible
            sizes.append(int(300 * max(1.0, spacing)))
        else:
            colors.append("orange")
            sizes.append(int(900 * max(1.0, spacing)))

    # compute figure size: allow override, otherwise scale with widest layer and number of layers
    if figsize:
        fig_w, fig_h = figsize
    else:
        widest = max((len(layer) for layer in layers), default=1)
        fig_w = max(12, int(3 + widest * 1.5 * spacing))
        fig_h = max(8, int(2 + len(layers) * 2.0))

    plt.figure(figsize=(fig_w, fig_h))
    # increase font sizes so labels are readable
    base_font = max(8, int(8 * max(1.0, spacing)))
    # Build labels that include host IPs where available (host name on first line, IP on second)
    labels = {}
    # Also print a concise mapping of host -> IP to the console for easy reference
    host_ip_list = []
    for n in G.nodes():
        if node_types.get(n) == 'host':
            ent = entities.get(n)
            ip = None
            try:
                ip = getattr(ent, 'ip_address', None)
            except Exception:
                ip = None
            ip_str = str(ip) if ip is not None else ''
            # two-line label: 'name\nip' to place IP clearly under the host name
            labels[n] = f"{n}\n{ip_str}" if ip_str else n
            host_ip_list.append((n, ip_str))
        else:
            labels[n] = n

    if host_ip_list:
        print("Hosts and IP addresses:")
        for hn, hip in host_ip_list:
            print(f"  {hn}: {hip if hip else '<no IP>'}")

    # draw nodes and edges first (without labels), then draw our custom labels so IPs appear
    nx.draw(G, pos, with_labels=False, node_color=colors, node_size=sizes)
    # Explicitly annotate host nodes using matplotlib.text so IPs show reliably
    ax = plt.gca()
    # estimate a vertical offset relative to figure height for label placement
    # increase offset to place labels further away from node markers so they are readable
    # positions are normalized (0..1), use a larger offset
    y_offset = 0.06 * max(1.0, spacing)
    sample = list(labels.items())[:10]
    if sample:
        print("Sample node labels to be drawn:")
        for k, v in sample:
            print(f"  {k}: {v}")
    for node, lab in labels.items():
        # draw labels for each node: hosts get their name and IP, switches get simple labels
        x, y = pos.get(node, (0.5, 0.5))
        if node_types.get(node) == 'host':
            # host label may be multi-line: keep as provided
            # if the node is too close to the bottom of the plot, draw label above node instead
            draw_above = False  # (y - y_offset) < 0.02
            label_y = (y + y_offset) if draw_above else (y - y_offset)
            valign = 'bottom' if draw_above else 'top'
            try:
                ax.text(x, label_y, lab, horizontalalignment='center', verticalalignment=valign,
                        fontsize=base_font, color='black',
                        bbox=dict(facecolor='white', alpha=0.95, edgecolor='none', pad=0.3))
            except Exception:
                # fallback to simple label
                ax.text(x, label_y, lab, horizontalalignment='center', verticalalignment=valign,
                        fontsize=base_font, color='black')
        else:
            # draw switch labels above or centered
            try:
                ax.text(x, y + (y_offset / 2), lab, horizontalalignment='center', verticalalignment='bottom',
                        fontsize=base_font, color='black',
                        bbox=dict(facecolor='white', alpha=0.85, edgecolor='none', pad=0.3))
            except Exception:
                ax.text(x, y + (y_offset / 2), lab, horizontalalignment='center', verticalalignment='bottom',
                        fontsize=base_font, color='black')
    # Expand axes limits so labels near borders are not clipped
    try:
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        if xs and ys:
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            pad_x = 0.05 * max(1.0, spacing)
            pad_y = 0.08 * max(1.0, spacing)
            ax.set_xlim(x_min - pad_x, x_max + pad_x)
            ax.set_ylim(y_min - pad_y, y_max + pad_y)
    except Exception:
        pass
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=max(6, int(base_font * 0.75)))

    saved_path = None
    if save:
        if path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"topology_{name}_{timestamp}.png"
        plt.savefig(path, bbox_inches='tight')
        saved_path = path
        print(f"Topology saved to {path}")
        # Also save host -> IP mapping next to the PNG for easy inspection
        if host_ip_list:
            try:
                hosts_path = os.path.splitext(path)[0] + "_hosts.txt"
                with open(hosts_path, 'w', encoding='utf-8') as fh:
                    fh.write('Hosts and IP addresses:\n')
                    for hn, hip in host_ip_list:
                        fh.write(f"{hn}: {hip if hip else '<no IP>'}\n")
                print(f"Host IP mapping saved to {hosts_path}")
            except Exception:
                pass
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
