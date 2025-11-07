import itertools
import random
from dataclasses import field, dataclass
from typing import Callable, Optional

# Use package-relative import so tests and imports from `infra` work correctly
from des.priority_queue import MinValuePriorityQueue


@dataclass(order=True)
class DESEvent:
    time: float
    seq: int = field(compare=False)
    action: Callable[[], None] = field(compare=False)


class DiscreteEventSimulator:

    def __init__(self, seed: int = 2908):
        self.current_time = 0.0
        self.event_queue: MinValuePriorityQueue = MinValuePriorityQueue()
        self.seq_counter = itertools.count()
        self.random_generator = random.Random(seed)

    def schedule_event(self, delay: float, action: Callable[[], None]) -> None:
        """Schedule an event to occur after a certain delay."""
        assert delay >= 0
        event_time = self.current_time + delay
        event = DESEvent(event_time, next(self.seq_counter), action)
        self.event_queue.enqueue(event)

    def run(self, until: Optional[float] = None) -> None:
        """Run the simulation until there are no more events."""
        while self.event_queue:
            event = self.event_queue.dequeue()
            if until is not None and event.time > until:
                print("Re-enqueueing event for future processing")
                self.event_queue.enqueue(event)
                self.current_time = until
                print("Simulation time advanced to", until)
                break
            # this is the earliest event to process
            self.current_time = event.time
            event.action()

    def get_current_time(self) -> float:
        return self.current_time
