import random
import logging
import argparse
import sys
from typing import List

from pkg_resources import empty_provider

from network_simulation.simulator_creator import SimulatorCreator
from scenarios.fat_tree_topo_creator import FatTreeTopoCreator
from scenarios.hsh_creator import HSHCreator
from scenarios.simple_star_creator import SimpleStarCreator
from network_simulation.stats import compute_run_stats, extract_topology_info




def create_creators_from_args(args) -> List[SimulatorCreator]:
    results: List[SimulatorCreator] = []
    visualize = args.v
    topology = args.t.lower()
    link_failures = args.link_failure
    if link_failures is None or len(link_failures) == 0:
        link_failures = [0.0]

    if topology == 'fat-tree':
        k = args.k
        if k is None:
            raise ValueError("k parameter must be supplied for fat-tree topology")
        if len(k) == 0:
            raise ValueError("k parameter list cannot be empty for fat-tree topology")
        for k in args.k:
            if k < 1 or (k % 2) != 0:
                raise ValueError("k must be >=1 and even for fat-tree topologies")
        for k in args.k:
            for link_failure in link_failures:
                logging.info(f"Creating Fat-Tree topology with k={k} ports per switch and link-failure={link_failure}%")
                results.append(FatTreeTopoCreator(k=k, max_path=1000000, visualize=visualize, link_failure_percent=link_failure))
    elif topology == 'hsh':
        for link_failure in link_failures:
            logging.info(f"Creating HSH topology with link-failure={link_failure}%")
            results.append(HSHCreator(visualize, link_failure_percent=link_failure, max_path=3))
    elif topology == 'simple-star':
        for link_failure in link_failures:
            logging.info(f"Creating Simple Star topology with link-failure={link_failure}%")
            results.append(SimpleStarCreator(visualize, link_failure_percent=link_failure, max_path=6))
    else:
        raise ValueError(f"Unknown topology '{args.t}'. Valid options: fat-tree, hsh, simple-star")

    return results


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Network simulator runner')
    parser.add_argument('-t', required=True,
                        help='Type of topology: fat-tree, hsh, simple-star')
    parser.add_argument('-k', nargs='+', type=int, default=None,
                        help='(fat-tree only) list of number of ports per switch (must be even)')
    parser.add_argument('-v', '--visualize', action='store_true', dest='v',
                        help='Enable topology visualization (single boolean flag)')
    parser.add_argument('-link-failure', nargs='+', type=float, default=0.0,
                        help='list of probability of links to fail in each test. Fraction (0-100) of links to fail')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    logging.info(f"Starting network simulation. topology={args.t}, k={args.k}, visualize={args.v}")
    logging.info(f"Link-failure percent parameter : {args.link_failure}")

    creators = create_creators_from_args(args)
    for creator in creators:
        simulator = creator.create_simulator()
        simulator.run()
        # collect messages that were created during the run
        messages = simulator.messages
        topology = extract_topology_info(creator.entities, creator.links)
        stats = compute_run_stats(messages, topology, simulator, creator.links)
        message = "\n".join(f"{k}: {v}" for k, v in stats.items())
        logging.info(f"Simulation stats: \n {message}")


def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # log to file for full debug trace
    file_handler = logging.FileHandler("simulation.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
        datefmt="%H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


if __name__ == '__main__':
    set_logger()
    random.seed(1972)
    try:
        main(sys.argv[1:])
    except Exception as e:
        logging.exception("Simulation failed with an exception")
        raise
