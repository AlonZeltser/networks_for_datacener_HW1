from des.des import DiscreteEventSimulator


def test_run_without_until_executes_all_events_and_advances_time():
    sim = DiscreteEventSimulator()
    calls = []

    def make_action(name):
        return lambda: calls.append((name, sim.current_time))

    sim.schedule_event(1.0, make_action("a"))
    sim.schedule_event(2.5, make_action("b"))

    sim.run()

    # Both actions should have run in time order
    assert calls == [("a", 1.0), ("b", 2.5)]
    # Simulator current time should be the time of the last event
    assert sim.current_time == 2.5


def test_run_with_until_stops_and_leaves_future_events_in_queue():
    sim = DiscreteEventSimulator()
    calls = []

    def make_action(name):
        return lambda: calls.append((name, sim.current_time))

    sim.schedule_event(1.0, make_action("a"))
    sim.schedule_event(5.0, make_action("b"))

    # Run only until time 2.0: only the first event should execute
    sim.run(until=2.0)

    assert calls == [("a", 1.0)]
    # current_time should be set to the `until` value
    assert sim.current_time == 2.0

    # The future event should still be in the queue (so run again without until runs it)
    sim.run()
    assert calls == [("a", 1.0), ("b", 5.0)]
    assert sim.current_time == 5.0

