import argparse
import socket
import sys
import threading
import time
from packet import Packet

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 9999
MAX_MSG_SIZE = 0
CLIENT_BUFFER_SIZE = 1024


def handle_file_input(file_path: str) -> int:
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
    try:
        maximum_msg_size = int(
            input("Enter the maximum message size (Bytes): "))
        return maximum_msg_size
    except ValueError:
        print("Error: Invalid input. Please enter valid integers as string.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    sys.exit(1)


def handle_client(client_socket: socket.socket, addr: tuple[str, int]):
    print(f"Connection from {addr} has been established.")
    with client_socket:
        # Send the max message size to the client
        msg_max_size = str(MAX_MSG_SIZE).encode()
        client_socket.sendall(msg_max_size)

        packets = []

        while True:
            try:
                data = client_socket.recv(MAX_MSG_SIZE + Packet.HEADER_SIZE)
                if not data:
                    break
                try:  # Unpack the received data
                    packet = Packet.unpack(data)
                    ack = handle_acknowledgement(packets, packet)
                    client_socket.sendall(ack.to_bytes(4, 'big'))

                except Exception as e:
                    print(f"Error occurred while unpacking the packet: {e}")
                    break
            except socket.error as e:
                print(f"Error occurred: {e}")
                break

        # Check validity of the packets
        if not packets or None in packets:
            print("Error: Some packets are missing.")
            return
        # Combine the packets
        message_bytes = b''.join(list(map(lambda x: x.data, packets)))
        message = message_bytes.decode()
        print(f"Message received: {message}")


def handle_acknowledgement(packets: list[Packet], packet: Packet) -> int:
    seq_num = packet.seq_num
    packets_len = len(packets)
    if seq_num == packets_len:
        packets.append(packet)
    elif seq_num > packets_len:
        packets.extend([None for _ in range((seq_num - packets_len))])
        packets.append(packet)
    else:
        if not packets[seq_num]:
            packets[seq_num] = packet

    if None in packets:
        return (packets.index(None) - 1)
    else:
        return (packets_len - 1)


def create_server_socket(address: str, port: int):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            server_socket.bind((address, port))
            server_socket.listen()
            server_socket.settimeout(12)
            print(f"Server is listening on {address}:{port}")

            threads = []

            while True:
                print("Waiting for a connection...")
                client_socket, addr = server_socket.accept()

                t = threading.Thread(target=handle_client,
                                     args=(client_socket, addr))
                t.start()
                threads.append(t)

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

    pass


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Reliable Ordered Data Transfer Server')

    parser.add_argument('-p', '--port', type=int,
                        default=DEFAULT_PORT, help='Port number to bind to')
    parser.add_argument('-a', '--address', type=str,
                        default=DEFAULT_HOST, help='IP Address to bind to')

    parser.add_argument('-f', '--file', type=str, default=None, help="""
                        File containing the attributes for the server.
                        The file should be located inside the current folder
                        or the full path should be provided.

                        Example input from file:

                        message:"This is a test message" 
                        maximum_msg_size:400 
                        window_size:4 
                        timeout:5
                        """)

    args = parser.parse_args()

    if args.file:
        maximum_msg_size = handle_file_input(args.file)
    else:
        maximum_msg_size = handle_user_input()

    print(f"{maximum_msg_size}")

    MAX_MSG_SIZE = maximum_msg_size

    print(MAX_MSG_SIZE)

    print("Initializing server...")

    create_server_socket(args.address, args.port)

    pass
