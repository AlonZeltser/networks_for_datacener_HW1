import random
import logging

from numpy.f2py.capi_maps import load_f2cmap_file

from scenarios.fat_tree_topo_creator import FatTreeTopoCreator
from scenarios.hsh_creator import HSHCreator
from scenarios.simple_star_creator import SimpleStarCreator


def simple_star_simulation():
    ssc = SimpleStarCreator(visualize=True, visualize_show=True, visualize_save=True)
    simulator = ssc.create_simulator()
    simulator.run()

def hsh_simulation():
    hsh = HSHCreator(visualize=True)
    simulator = hsh.create_simulator()
    simulator.run()


def fat_tree_simulation():
    # enable visualization: show the plot and save it to a file
    fts = FatTreeTopoCreator(k=4, visualize=False, visualize_show=True, visualize_save=True)
    logging.info("creating fat tree simulator...")
    simulator = fts.create_simulator()
    logging.info("running fat tree simulation...")
    simulator.run()
    logging.info("fat tree simulation completed.")


def main():
    logging.info("Starting network simulations...")
    fat_tree_simulation()
    #hsh_simulation()
    #simple_star_simulation()
    logging.info("Finished network simulations.")

def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
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
    main()
