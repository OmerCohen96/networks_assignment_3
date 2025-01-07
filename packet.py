import struct
import time


class Packet:

    """
    A class to represent a network packet for reliable data transfer.

    The Packet class encapsulates the data and metadata required for 
    reliable, ordered data transfer over a network. It includes a 
    sequence number, acknowledgment flag, timestamp, and the actual 
    data payload. The class provides methods to pack and unpack the 
    packet data for transmission over a network socket.

    Attributes:
    ----------
    seq_num : int
        The sequence number of the packet.
        Or the acknowledgment number of the packet if it is an acknowledgment message.
    ack_msg : bool
        A flag indicating whether the packet is an acknowledgment message.
    timestamp : float
        The timestamp when the packet was created.
    data : bytes
        The actual data payload of the packet.

    Methods:
    -------
    pack() -> bytes:
        Packs the packet attributes into a bytes object for transmission.
    unpack(packet: bytes) -> 'Packet':
        Unpacks a bytes object into a Packet instance.
    __str__() -> str:
        Returns a string representation of the packet.
    """

    HEADER_FORMAT = 'I?d'

    # The size of the packet header in bytes (Without the data payload)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, seq_num: int, ack_msg: bool = False, timestamp: float = None, data: bytes = b''):
        self.seq_num = seq_num
        self.ack_msg = ack_msg
        self.timestamp = timestamp if timestamp is not None else time.time()
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
