from typing import List, Dict, Any, Tuple
from network_simulation.message import Message
from network_simulation.link import Link

def _mean(values: List[float]) -> float:
    return float(sum(values)) / float(len(values)) if values else 0.0


def compute_run_stats(messages: List[Message], topology: Dict[str, Any], scheduler:Any, links:List[Any]) -> Dict[str, Any]:

    messages_count = len(messages)
    delivered_straight = 0
    delivered_while_lost = 0
    dropped_count = 0
    path_lengths = []

    total_time = scheduler.end_time

    for m in messages:
        assert not (m.delivered and m.dropped), "Message cannot be both delivered and dropped"
        # support either object with attributes or dict
        if m.delivered:
            if m.lost:
                delivered_while_lost += 1
            else:
                delivered_straight += 1
            path_lengths.append(len(m.path))
        elif m.dropped:
            dropped_count += 1

    avg_path = float(_mean(path_lengths)) if path_lengths else 0.0
    max_path = max(path_lengths) if path_lengths else 0
    min_path = min(path_lengths) if path_lengths else 0
    dropped_percentage = (dropped_count / messages_count * 100.0) if messages_count > 0 else 0.0
    delivered_straight_percentage = (delivered_straight / messages_count * 100.0) if messages_count > 0 else 0.0
    delivered_while_lost_percentage = (delivered_while_lost / messages_count * 100.0) if messages_count > 0 else 0.0

    total_links = len(links)
    total_delivery_time = 0.0
    min_delivery_time = float("inf")
    max_delivery_time = 0.0
    min_delivery_bytes = float("inf")
    max_delivery_bytes = 0
    total_bytes = 0
    for link in links:
        min_delivery_time = min(min_delivery_time, link.accumulated_transmitting_time)
        max_delivery_time = max(max_delivery_time, link.accumulated_transmitting_time)
        total_delivery_time += link.accumulated_transmitting_time
        min_delivery_bytes = min(min_delivery_bytes, link.accumulated_bytes_transmitted)
        max_delivery_bytes = max(max_delivery_bytes, link.accumulated_bytes_transmitted)
        total_bytes += link.accumulated_bytes_transmitted

    link_average_time = (total_delivery_time / total_links) if total_links > 0 else 0.0
    link_average_utlization = (total_delivery_time / (total_links * total_time)) * 100.0 if total_links > 0 and total_time > 0 else 0.0
    link_average_bytes = (total_bytes / total_links) if total_links > 0 else 0.0


    failed_links = topology.get('failed_links', []) or []
    switches = set(topology.get('switches', []) or [])
    switches_with_failed_link = set()
    for link in failed_links:
        # link represented as object or tuple (a,b) or link.name
        if isinstance(link, tuple) or isinstance(link, list):
            a, b = link
            if a in switches:
                switches_with_failed_link.add(a)
            if b in switches:
                switches_with_failed_link.add(b)
        else:
            # could be link name like 's1-s2'; try splitting
            try:
                parts = str(link).split('-')
                for p in parts:
                    if p in switches:
                        switches_with_failed_link.add(p)
            except Exception:
                pass

    stats = {
        'total_time': total_time,
        'delivered_straight_count': delivered_straight,
        'delivered_straight_percentage': delivered_straight_percentage,
        'delivered_while_lost_count': delivered_while_lost,
        'delivered_while_lost_percentage': delivered_while_lost_percentage,
        'dropped_count': dropped_count,
        'dropped_percentage': dropped_percentage,
        'link_average_delivery_time': link_average_time,
        'link_min_delivery_time': min_delivery_time if min_delivery_time != float("inf") else 0.0,
        'link_max_delivery_time': max_delivery_time,
        'link_average_utilization_percent': link_average_utlization,
        'link_min_bytes_transmitted': min_delivery_bytes if min_delivery_bytes != float("inf") else 0,
        'average_path_length': avg_path,
        'max_path_length': max_path,
        'min_path_length': min_path,
        'switches_with_failed_link': len(switches_with_failed_link),
        'num_failed_links': len(failed_links),
        'num_hosts': len(topology.get('hosts', []) or []),
        'num_switches': len(topology.get('switches', []) or []),
        'num_links': len(topology.get('links', []) or []),
        'total_messages': messages_count,
    }
    return stats


def extract_topology_info(entities: Dict[str, Any], links: List[Any]) -> Dict[str, Any]:
    hosts = []
    switches = []
    link_names = []
    failed_links = []
    for name, ent in entities.items():
        # heuristics based on class names
        cls_name = ent.__class__.__name__
        if cls_name == 'Host':
            hosts.append(name)
        elif cls_name == 'Switch':
            switches.append(name)
        elif cls_name == 'Link':
            link_names.append(getattr(ent, 'name', name))
            if getattr(ent, 'failed', False):
                failed_links.append((getattr(ent, 'node1').name if getattr(ent, 'node1', None) is not None else None,
                                     getattr(ent, 'node2').name if getattr(ent, 'node2', None) is not None else None))

    return {
        'hosts': hosts,
        'switches': switches,
        'links': link_names,
        'failed_links': failed_links,
    }
