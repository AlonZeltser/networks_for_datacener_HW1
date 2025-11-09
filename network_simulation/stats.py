from typing import List, Dict, Any, Tuple

# Avoid importing the stdlib `statistics` module because this repository contains a
# top-level `statistics` package that shadows the standard library. Implement a
# tiny local mean helper instead.

def _mean(values: List[float]) -> float:
    return float(sum(values)) / float(len(values)) if values else 0.0


def compute_run_stats(messages: List[Dict[str, Any]], topology: Dict[str, Any], include_lost_in_path_stats: bool = False) -> Dict[str, Any]:
    """Compute run statistics.

    messages: list of message-like dicts or objects with attributes 'path' (list) and 'delivered' (bool)
    topology: dict with keys 'hosts', 'switches', 'links', 'failed_links' (lists)
    """
    total = len(messages)
    delivered_count = 0
    lost_count = 0
    path_lengths = []

    for m in messages:
        # support either object with attributes or dict
        delivered = getattr(m, 'delivered', None)
        if delivered is None and isinstance(m, dict):
            delivered = m.get('delivered', False)
        if delivered:
            delivered_count += 1
        else:
            lost_count += 1

        if include_lost_in_path_stats or delivered:
            p = getattr(m, 'path', None)
            if p is None and isinstance(m, dict):
                p = m.get('path', [])
            path_lengths.append(len(p or []))

    avg_path = float(_mean(path_lengths)) if path_lengths else 0.0
    max_path = max(path_lengths) if path_lengths else 0
    min_path = min(path_lengths) if path_lengths else 0
    pct_lost = (lost_count / total * 100.0) if total > 0 else 0.0

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
        'average_path_length': avg_path,
        'max_path_length': max_path,
        'min_path_length': min_path,
        'percent_messages_lost': pct_lost,
        'switches_with_failed_link': len(switches_with_failed_link),
        'num_failed_links': len(failed_links),
        'num_hosts': len(topology.get('hosts', []) or []),
        'num_switches': len(topology.get('switches', []) or []),
        'num_links': len(topology.get('links', []) or []),
        'total_messages': total,
        'delivered_messages': delivered_count,
        'lost_messages': lost_count,
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
