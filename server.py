import argparse
import socket
import sys
import threading
import time
from packet import Packet
import signal

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 9999
MAX_MSG_SIZE = 0
CLIENT_BUFFER_SIZE = 1024

stop_server = False


def signal_handler(sig, frame):
    global stop_server
    print("Shutting down server...")
    stop_server = True


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def handle_acknowledgement(packets: list[Packet], packet: Packet) -> int:
    seq_num = packet.seq_num
    packets_len = len(packets)
    if seq_num == packets_len:
        packets.append(packet)
    elif seq_num > packets_len:
        packets.extend([None for _ in range((seq_num - packets_len))])
        packets.append(packet)
    elif packets[seq_num] is None:
        packets[seq_num] = packet

    for i, pkt in enumerate(packets):
        if pkt is None:
            print(f"there is none! function returning {i - 1}")
            return i - 1
    print(f"no none!   function returning {len(packets) - 1}")
    return (len(packets) - 1)


def handle_client(client_socket: socket.socket, addr: tuple[str, int]):
    print(f"Connection from {addr} has been established.")
    with client_socket:
        # Send the max message size to the client
        msg_max_size = str(MAX_MSG_SIZE).encode()
        client_socket.sendall(msg_max_size)

        packets = []

        running = True

        while running and not stop_server:
            try:
                data = client_socket.recv(MAX_MSG_SIZE + Packet.HEADER_SIZE)
                if not data:
                    break
                try:  # Unpack the received data
                    packet = Packet.unpack(data)

                    if packet.ack_msg == True:
                        break

                    ack_number = handle_acknowledgement(packets, packet)
                    print(f"ack: {ack_number} received")
                    # input(f"Sending ack: {ack} ...")

                    if ack_number >= 0:
                        ack_packet = Packet(ack_number, ack_msg=True)
                        client_socket.sendall(ack_packet.pack())
                except KeyboardInterrupt:
                    print("Shutting down...")
                    running = False
                    sys.exit(1)
                    break

                except Exception as e:
                    print(f"Error occurred while unpacking the packet: {e}")
                    break
            except socket.error as e:
                print(f"Error occurred: {e}")
                break

        # Check validity of the packets
        if not packets or None in packets:
            print("Error: Some packets are missing.")
            sys.exit(1)
        # Combine the packets
        message_bytes = b''.join(list(map(lambda x: x.data, packets)))
        message = message_bytes.decode()
        print(f"Message received: {message}")


def initialize_server_socket(address: str, port: int):

    # Create a server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            server_socket.bind((address, port))
            server_socket.listen()
            print(f"Server is listening on {address}:{port}")

            server_socket.settimeout(300)
            threads = []

            print("Waiting for a connection...")

            running = True

            while running and not stop_server:
                try:
                    client_socket, addr = server_socket.accept()

                    t = threading.Thread(target=handle_client,
                                         args=(client_socket, addr))
                    t.start()
                    threads.append(t)
                except KeyboardInterrupt:
                    print("Shutting down...")
                    running = False
                    break

        except socket.timeout:
            print("Error: Connection timed out.")
            sys.exit(1)
        except OSError as e:
            print(f"Error: {e}")
            sys.exit(1)
        finally:
            print("Closing server socket...")
            for t in threads:
                t.join()


def handle_file_input(file_path: str) -> int:
    """Read the file and extract the maximum message size from it."""
    try:
        with open(file_path, 'r') as file:
            data = file.read().split('\n')
            maximum_msg_size = int(data[1].split(':')[1].strip())
        return maximum_msg_size
    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except IndexError:
        print("Error: The file format is incorrect.")
    except ValueError:
        print("Error: Could not convert data to an integer.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    sys.exit(1)


def handle_user_input() -> int:
    """Prompt the user to enter the maximum message size."""
    try:
        maximum_msg_size = int(
            input("Enter the maximum message size (Bytes): "))
        return maximum_msg_size
    except ValueError:
        print("Error: Invalid input. Please enter valid integers as string.")
    except Exception as e:
        print(f"An unexpected error occurred while reading the input: {e}")
    sys.exit(1)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Reliable Ordered Data Transfer Server',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('-p', '--port', type=int,
                        default=DEFAULT_PORT, help='Port number to bind to')
    parser.add_argument('-a', '--address', type=str,
                        default=DEFAULT_HOST, help='IP Address to bind to')

    # Adding an option to retrieve the requested file as described in the task requirements
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
    # Otherwise, prompt the user to enter the
    # maximum message size (The only relevant attribute for the server)
    if args.file:
        maximum_msg_size = handle_file_input(args.file)
    else:
        maximum_msg_size = handle_user_input()

    # DELETE THIS LINE ========================================================
    print(f"{maximum_msg_size}")

    MAX_MSG_SIZE = maximum_msg_size

    # DELETE THIS LINE ========================================================
    print(MAX_MSG_SIZE)

    print("Initializing server...")

    initialize_server_socket(args.address, args.port)

    # End point of the program
    print("Server has been closed.")
