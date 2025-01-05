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
LAST_ACKNOWLEDGED = -1


def handle_acknowledgement(client_socket: socket.socket, last_ack: int):
    global LAST_ACKNOWLEDGED
    while True:
        try:
            packet_data = client_socket.recv(Packet.HEADER_SIZE)
            if not packet_data:
                break
            packet = Packet.unpack(packet_data)
            ack_number = packet.seq_num
            print(f"ack: {ack_number} received")

            if ack_number > LAST_ACKNOWLEDGED:
                LAST_ACKNOWLEDGED = ack_number
            elif ack_number == last_ack:
                break
            else:
                print("Duplicate acknowledgment received.")
        except ValueError:
            print("Error: Could not convert data to an integer.")
            sys.exit(1)
        except Exception as e:
            print(f"Error in handle_acknowledgement: {e}")
            sys.exit(1)


def send_packet(seq_num, fragment, client_socket: socket.socket):
    """ Sends a packet to the server and returns the packet object """
    packet = Packet(seq_num, data=fragment)
    client_socket.sendall(packet.pack())
    print(f"Packet {seq_num} sent.")
    return packet


def handle_reliable_transmission(client_socket: socket.socket, message_fragments: list[bytes]):
    with client_socket:
        window = deque(maxlen=SLIDING_WINDOW_SIZE)
        acked_packets = -1
        last_ack = len(message_fragments) - 1

        # Start the acknowledgment handler thread
        ack_thread = threading.Thread(
            target=handle_acknowledgement, args=(client_socket, last_ack))
        ack_thread.start()

        while acked_packets < last_ack:
            if window and window[-1].seq_num < last_ack:
                acked_packets = LAST_ACKNOWLEDGED

                while window and window[0].seq_num <= acked_packets:
                    window.popleft()

                if not window:
                    continue
                elif len(window) == SLIDING_WINDOW_SIZE:
                    if time.time() - window[0].timestamp > TIMEOUT:
                        print(f"Timeout: Resending all packets in the window")
                        for i in range(SLIDING_WINDOW_SIZE):
                            print(f"Resending packet {window[0].seq_num}")
                            re_send_packet = window.popleft()
                            window.append(send_packet(
                                re_send_packet.seq_num, re_send_packet.data, client_socket))
                else:
                    next_seq = window[-1].seq_num + 1
                    while len(window) < SLIDING_WINDOW_SIZE and next_seq < last_ack:
                        packet = send_packet(
                            next_seq, message_fragments[next_seq], client_socket)
                        window.append(packet)
                        next_seq += 1

            elif not window:
                acked_packets = LAST_ACKNOWLEDGED
                i = acked_packets
                while i < last_ack and len(window) < SLIDING_WINDOW_SIZE:
                    i += 1
                    packet = send_packet(
                        i, message_fragments[i], client_socket)
                    window.append(packet)

            time.sleep(0.1)
            acked_packets = LAST_ACKNOWLEDGED

    print("All fragments sent.")
    ack_thread.join()


def initiate_connection(server_address: str, server_port: int, message: str):

    print(f"Connecting to server at {server_address}:{server_port}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            # Connect to the server
            client_socket.connect((server_address, server_port))

            # Initialize the max payload size the server can handle
            max_payload_size = 0

            # Receive the max payload size from the server
            max_payload_size = client_socket.recv(BUFFER_SIZE).decode()
            max_payload_size = int(max_payload_size)

            # if the server can not recive any data
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
        # than, returns the message fragments as a bytes array
        message_fragments = split_message_into_fragments(
            message, max_payload_size)

        print(f"Sending {len(message_fragments)} fragments to the server.")

        # initiate the reliable transmission of the message fragments
        handle_reliable_transmission(client_socket, message_fragments)

    print("Connection closed.")


def split_message_into_fragments(message: str, max_payload_size: int) -> list[bytes]:
    """Splits the message into byte fragments of max payload size that the server can handle"""
    msg_bytes = message.encode()
    msg_bytes_len = len(msg_bytes)

    # Split the message into fragments of max payload size
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
            timeout = int(data[3].split(':')[1].strip())
        return message, window_size, timeout
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except IndexError:
        print("Error: The file format is incorrect.")
    except ValueError:
        print("Error: Could not convert data to an integer.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    sys.exit(1)


def handle_user_input() -> tuple[str, int, int]:
    """Prompts the user to enter the message, window size, and timeout values"""
    try:
        message = input("Enter the message: ")
        window_size = int(input("Enter the window size: "))
        timeout = int(input("Enter the timeout: "))
        return message, window_size, timeout
    except ValueError:
        print("Error: Invalid input. Please enter valid integers as string.")
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

    # If the file option is provided, read the file and extract the maximum message size
    # Otherwise, prompt the user to enter the relevant attributes
    if args.file:
        message, window_size, timeout = handle_file_input(args.file)
    else:
        message, window_size, timeout = handle_user_input()

    # Check if the window size and timeout are valid
    # window size and timeout must be greater than 0
    # the desired behavior for invalid values is not specified
    if window_size < 1 or timeout < 1:
        print("Error: Window size and timeout must be greater than 0.")
        print("Exiting...")
        sys.exit(1)

    # Set the global variables
    SLIDING_WINDOW_SIZE = window_size
    TIMEOUT = timeout

    print("Starting the connection...")

    print(f"Message: {message} {len(message)}")

    initiate_connection(args.address, args.port, message)

    # End point of the program
    print("Message sent successfully. connection is closed.")
