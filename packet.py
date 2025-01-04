import struct
import time


class Packet:
    HEADER_FORMAT = 'Id'
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, seq_num: int, timestamp: float = time.time(), data: bytes = b''):
        self.seq_num = seq_num
        self.timestamp = timestamp
        self.data = data

    def pack(self) -> bytes:
        return struct.pack(self.HEADER_FORMAT, self.seq_num, self.timestamp) + self.data

    @classmethod
    def unpack(cls, packet: bytes) -> 'Packet':
        try:
            seq_num, timestamp = struct.unpack(
                cls.HEADER_FORMAT, packet[:cls.HEADER_SIZE])
            return cls(seq_num, timestamp=timestamp, data=packet[cls.HEADER_SIZE:])
        except struct.error as e:
            raise ValueError("Failed to unpack the packet") from e
