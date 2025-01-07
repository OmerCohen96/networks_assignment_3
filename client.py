import sys
import socket
import time
import argparse
from packet import Packet
from collections import deque
import threading

DEFAULT_SERVER_HOST = '127.0.0.1'
DEFAULT_SERVER_PORT = 9999
# The initial buffer size for receiving server max payload size and acknowledgements
BUFFER_SIZE = 1024
SLIDING_WINDOW_SIZE = 0
TIMEOUT = 0
# The last acknowledged packet by the server
# Start with -1 to indicate that no packets have been acknowledged yet
LAST_ACKNOWLEDGED = -1


def handle_acknowledgement(connection_socket: socket.socket, last_ack: int) -> None:
    """
    Handles the reception and processing of acknowledgment packets from the server.

    This function runs in a separate thread and continuously listens for acknowledgment
    packets from the server. It updates the global LAST_ACKNOWLEDGED variable with the
    highest sequence number acknowledged by the server. If all packets have been acknowledged,
    it sends a final acknowledgment to the server and terminates.

    last_ack : int
        The sequence number of the last packet to be acknowledged.
    """
    global LAST_ACKNOWLEDGED
    while True:
        try:
            # Check if the LAST_ACKNOWLEDGED is equal to the last_ack
            # If so, all packets have been acknowledged
            if LAST_ACKNOWLEDGED == last_ack:
                print("All packets have been acknowledged.")

                # Send a packet that indicates the last packet has been acknowledged
                connection_socket.sendall(
                    Packet(last_ack, ack_msg=True).pack())
                break

            # Receive the acknowledgments from the server
            packet_data = connection_socket.recv(Packet.HEADER_SIZE)
            if not packet_data:
                break
            packet = Packet.unpack(packet_data)

            # Extract the sequence number from the acknowledgment packet
            ack_number = packet.seq_num
            print(f"ack: {ack_number} received")

            # Update the LAST_ACKNOWLEDGED just if the ack_number is greater than the current value
            if ack_number > LAST_ACKNOWLEDGED:
                LAST_ACKNOWLEDGED = ack_number
        except ValueError:
            print("Error: Could not convert data to an integer.")
            sys.exit(1)
        except socket.error as e:
            print(f"Error: An error occurred with the socket: {e}")
            break
        except Exception as e:
            print(f"Error in handle_acknowledgement: {e}")
            sys.exit(1)


def handle_reliable_transmission(client_socket: socket.socket, message_fragments: list[bytes]):
    with client_socket:

        # Initialize the sliding window
        window = deque(maxlen=SLIDING_WINDOW_SIZE)

        # Initialize the last acknowledged packet by the server
        last_acked_packet = -1
        last_sequence_number = len(message_fragments) - 1

        # Start the acknowledgment handler thread
        ack_thread = threading.Thread(
            target=handle_acknowledgement, args=(client_socket, last_sequence_number))
        ack_thread.start()

        # loop until all packets have been acknowledged
        while last_acked_packet < last_sequence_number:

            print(
                f"current Packet details in the window {[(x.seq_num , x.data) for x in window]}")

            if window and window[-1].seq_num <= last_sequence_number:
                last_acked_packet = LAST_ACKNOWLEDGED

                while len(window) < SLIDING_WINDOW_SIZE and window[-1].seq_num < last_sequence_number:
                    print("stack here 688", LAST_ACKNOWLEDGED)
                    packet = send_packet(
                        window[-1].seq_num + 1, message_fragments[window[-1].seq_num + 1], client_socket)
                    window.append(packet)

                while window and window[0].seq_num <= last_acked_packet:
                    print("stack here 63", LAST_ACKNOWLEDGED)
                    window.popleft()

                if not window:
                    continue
                elif len(window) == SLIDING_WINDOW_SIZE or window[-1].seq_num > last_acked_packet:
                    print("stack here 69", LAST_ACKNOWLEDGED)
                    time.sleep(2)
                    print(f"Timeout = {time.time() - window[0].timestamp}")
                    if time.time() - window[0].timestamp > TIMEOUT:
                        print(f"Timeout: Resending all packets in the window")
                        window_current_size = len(window)
                        for i in range(window_current_size):
                            print(f"Resending packet {window[0].seq_num}")
                            re_send_packet = window.popleft()
                            window.append(send_packet(
                                re_send_packet.seq_num, re_send_packet.data, client_socket))
                else:
                    next_seq = window[-1].seq_num + 1
                    print("stack here 89", LAST_ACKNOWLEDGED)
                    while len(window) < SLIDING_WINDOW_SIZE and next_seq < last_sequence_number:
                        print("stack here 80")
                        packet = send_packet(
                            next_seq, message_fragments[next_seq], client_socket)
                        window.append(packet)
                        next_seq += 1

            elif not window:
                last_acked_packet = LAST_ACKNOWLEDGED
                i = last_acked_packet
                while i < last_sequence_number and len(window) < SLIDING_WINDOW_SIZE:
                    print("stack here 91")
                    i += 1
                    packet = send_packet(
                        i, message_fragments[i], client_socket)
                    window.append(packet)
            print("stack here 103", LAST_ACKNOWLEDGED)

            time.sleep(0.0001)
            last_acked_packet = LAST_ACKNOWLEDGED

        ack_thread.join()

    print("All fragments sent.")


def initiate_connection(server_address: str, server_port: int, message: str) -> None:

    print(f"Connecting to server at {server_address}:{server_port}")

    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection_socket:
        try:
            # Connect to the server
            connection_socket.connect((server_address, server_port))

            # Initialize the max payload size the server can handle
            max_payload_size = 0

            # Receive the max payload size from the server
            # The server will send the max payload size as a string
            # we dont know the size of the max payload size
            # so we will receive the data in chunk of 1024 bytes
            max_payload_size = connection_socket.recv(BUFFER_SIZE).decode()

            # Convert the max payload size to an integer
            max_payload_size = int(max_payload_size)

            print(
                f"Max payload size that the server can handle: {max_payload_size}")

            # If the max payload size is 0, the server can not receive any data
            if not max_payload_size:
                print("Server can not recive any data.\n"
                      f"The maximum payload size that the server can handle is {max_payload_size}.\n"
                      "Exiting...")
                return

        except (ConnectionRefusedError, ConnectionAbortedError):
            print("Error: Connection was refused by the server.")
            return
        except ValueError:
            print("Error: Could not convert max payload size to an integer.")
            return
        except Exception as e:
            print(
                f"An unexpected error occurred while trying to connect to the server: {e}")
            return

        # Performs fragmentation on the message based on the max payload size.
        # then, returns the message fragments as a bytes array
        message_fragments = split_message_into_fragments(
            message, max_payload_size)

        print(f"Sending {len(message_fragments)} fragments to the server.")

        # Initiate and start the reliable transmission of the message fragments
        handle_reliable_transmission(connection_socket, message_fragments)
        time.sleep(1)

    print(
        f"Connection with the server at {server_address}:{server_port} closed.")


def send_packet(seq_num, fragment, socket_connection: socket.socket) -> 'Packet':
    """ Sends a packet to the server and returns the packet object """
    packet = Packet(seq_num, data=fragment, timestamp=time.time())

    # Send the packet to the server
    socket_connection.sendall(packet.pack())
    print(f"Packet {seq_num} sent.")
    return packet


def split_message_into_fragments(message: str, max_payload_size: int) -> list[bytes]:
    """Splits the message into byte fragments of max payload size that the server can handle"""
    msg_bytes = message.encode()
    msg_bytes_len = len(msg_bytes)

    # Split the message into fragments which are less than or equal to the max payload size
    fragments = [msg_bytes[i:i + max_payload_size]
                 for i in range(0, msg_bytes_len, max_payload_size)]
    return fragments


def handle_file_input(file_path: str) -> tuple[str, int, int]:
    """Reads the file and extracts the message, window size, and timeout values"""
    try:
        with open(file_path, 'r') as file:
            data = file.read().split('\n')
            message = data[0].split(':')[1].strip().strip('"\'').strip()
            window_size = int(data[2].split(':')[1].strip())
            timeout = float(data[3].split(':')[1].strip())
        return message, window_size, timeout
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except IndexError:
        print("Error: The file format is incorrect.")
    except ValueError:
        print("Error: Invalid input. Please enter valid integer for the window size and valid float/integer for timeout.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    sys.exit(1)


def handle_user_input() -> tuple[str, int, int]:
    """Prompts the user to enter the message, window size, and timeout values"""
    try:
        message = input("Enter the message: ")
        window_size = int(input("Enter the window size: "))
        timeout = float(input("Enter the timeout: "))
        return message, window_size, timeout
    except ValueError:
        print("Error: Invalid input. Please enter valid integer for the window size and \
              valid float/integer for timeout.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    sys.exit(1)


if "__main__" == __name__:

    parser = argparse.ArgumentParser(
        description="Client for the Reliable Data Transfer Protocol",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('-p', '--port', type=int,
                        default=DEFAULT_SERVER_PORT, help='Port number to connect to')
    parser.add_argument('-a', '--address', type=str,
                        default=DEFAULT_SERVER_HOST, help='IP Address to connect to')

    # Adding an option to retrieve the input file as described in the task requirements
    parser.add_argument('-f', '--file', type=str, default=None, help="""File containing the attributes for the server (for server.py and client.py modules).
The file should either be located inside the current folder
or the full path should be provided.
Also, the file must contain data that follows the following format:

message:<message>
maximum_msg_size:<maximum_msg_size>
window_size:<window_size>
timeout:<timeout>

Example:
message:"This is a test message" 
maximum_msg_size:400 
window_size:4 
timeout:5
                        
""")

    args = parser.parse_args()

    # If the file option is provided, read the file and extract relevant attributes
    # Otherwise, prompt the user to enter the those attributes
    if args.file:
        message, window_size, timeout = handle_file_input(args.file)
    else:
        message, window_size, timeout = handle_user_input()

    # Check if the window size and timeout that recievd are valid
    # window size should be integer greater than 1 and timeout must be greater than 0
    # the desired behavior for invalid values is not specified
    if window_size < 1 or timeout <= 0:
        print("Error: Window size and timeout must be greater than 0.")
        print("Exiting...")
        sys.exit(1)

    # Set the global variables
    SLIDING_WINDOW_SIZE = window_size
    TIMEOUT = timeout

    print(f"Message content for sending: {message}")

    print("Starting the connection...")

    initiate_connection(args.address, args.port, message)

    # End point of the program
    print("Exiting...")
