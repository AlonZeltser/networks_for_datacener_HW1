from abc import ABC, abstractmethod
from typing import List

from des.des import DiscreteEventSimulator
from network_simulation.message import Message


class Node(ABC):
    def __init__(self, name: str, scheduler: DiscreteEventSimulator):
        self.name = name
        self.scheduler = scheduler
        self.inbox: List[Message] = []

    # called by others, to make this actor receive a message
    def post(self, message: Message) -> None:
        message.path.append(self.name)
        self.inbox.append(message)
        self.scheduler.schedule_event(0.0, self.handle_message)

    # empty the inbox one by one, by scheduling handle_message events to this time step
    def handle_message(self):
        if self.inbox:
            message = self.inbox.pop(0)
            self.on_message(message)
            if self.inbox:
                self.scheduler.schedule_event(0.0, self.handle_message)

    @abstractmethod
    def on_message(self, message: Message):
        pass
