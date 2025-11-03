from scenarios.fat_tree_topo_creator import FatTreeTopoCreator
from scenarios.hsh_creator import HSHCreator


def hsh_simulation():
    hsh = HSHCreator()
    simulator = hsh.create_simulator()
    simulator.run()


def fat_tree_simulation():
    fts = FatTreeTopoCreator(k=4)
    simulator = fts.create_simulator()
    simulator.run()


def main():
    fat_tree_simulation()


if __name__ == '__main__':
    main()
