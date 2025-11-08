from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import xxhash

class Protocol(Enum):
    TCP = 1
    UDP = 2
    CONTROL = 3


@dataclass
class FiveTuple:
    src_ip: str
    dst_ip: str
    src_protocol_port: int
    dst_protocol_port: int
    protocol: Protocol
    def __str__(self) -> str:
        return (f"{self.src_ip}:{self.src_protocol_port} -> "
                f"{self.dst_ip}:{self.dst_protocol_port} ({self.protocol.name})")
    def __hash__(self) -> int:
        return xxhash.xxh64(str(self)).intdigest()


@dataclass
class Message:
    id: int
    sender_id: str
    receiver_id: str
    flow_id: int
    five_tuple: Optional[FiveTuple]
    size_bytes: int
    brith_time: float
    content: Any
    ttl: int = 64

    def is_expired(self, current_time: float) -> bool:
        return (current_time - self.brith_time) > self.ttl
