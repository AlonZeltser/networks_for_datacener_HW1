from scenarios.fat_tree_topo_creator import FatTreeTopoCreator
from scenarios.hsh_creator import HSHCreator


def hsh_simulation():
    hsh = HSHCreator(visualize=True)
    simulator = hsh.create_simulator()
    simulator.run()


def fat_tree_simulation():
    # enable visualization: show the plot and save it to a file
    fts = FatTreeTopoCreator(k=4, visualize=True, visualize_before_run=False, visualize_show=True, visualize_save=True)
    simulator = fts.create_simulator()
    simulator.run()


def main():
    fat_tree_simulation()
    #hsh_simulation()


if __name__ == '__main__':
    main()
