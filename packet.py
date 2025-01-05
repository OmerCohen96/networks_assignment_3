import struct
import time


class Packet:
    HEADER_FORMAT = 'I?d'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, seq_num: int, ack_msg: bool = False, timestamp: float = time.time(), data: bytes = b''):
        self.seq_num = seq_num
        self.ack_msg = ack_msg
        self.timestamp = timestamp
        self.data = data

    def pack(self) -> bytes:
        return struct.pack(self.HEADER_FORMAT, self.seq_num, self.ack_msg, self.timestamp) + self.data

    def __str__(self) -> str:
        return f"Packet(seq_num={self.seq_num}, ack_msg={self.ack_msg}, timestamp={self.timestamp}, data={self.data})"

    @classmethod
    def unpack(cls, packet: bytes) -> 'Packet':
        try:
            seq_num, ack_msg, timestamp = struct.unpack(
                cls.HEADER_FORMAT, packet[:cls.HEADER_SIZE])
            return cls(seq_num, ack_msg, timestamp=timestamp, data=packet[cls.HEADER_SIZE:])
        except struct.error as e:
            raise ValueError("Failed to unpack the packet") from e
