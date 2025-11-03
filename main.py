from des.des import DiscreteEventSimulator
from network_simulation.host import Host
from network_simulation.link import Link
from network_simulation.switch import Switch
from scenarios.hsh_creator import HSHCreator

"""
def _main():
    simulator = DiscreteEventSimulator()

    h1 = Host('Host1', simulator)
    h2 = Host('Host2', simulator)
    s1 = Switch('Switch1', simulator)

    link1 = Link("h1_s1", simulator, 1e6, 0.01)
    link2 = Link('h2_s1', simulator, 1e6, 0.01)

    h1.connect(link1, s1)
    s1.connect('port1', link1, h1)

    h2.connect(link2, s1)
    s1.connect('port2', link2, h2)

    h2.connect(link2, s1)

    s1.set_routing('Host2', 'port2')
    s1.set_routing('Host1', 'port1')

    def app():
        h1.send_to('Host2', b'Hello, Host2!', size_bytes=500)
        h1.send_to('Host2', b'bye bye, Host2!', size_bytes=500)
    simulator.schedule_event(0.1, app)
    simulator.run()
"""
def main():
    hsh = HSHCreator()
    simulator = hsh.create_simulator()
    simulator.run()

if __name__ == '__main__':
    main()