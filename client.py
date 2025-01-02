import sys
import socket
import threading
import time
import argparse

DEFAULT_SERVER_HOST = '127.0.0.1'
DEFAULT_SERVER_PORT = 9999
BUFFER_SIZE = 1024


def handle_file_input(file_path: str) -> tuple[str, int, int]:
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


def start_transmission(server_address: str, server_port: int, message: str, window_size: int, timeout: int):
    print(f"Connecting to server at {server_address}:{server_port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((server_address, server_port))

            # Initialize the max payload size
            max_payload_size = 0
            # Receive the max payload size from the server
            max_payload_size = client_socket.recv(BUFFER_SIZE).decode()
            max_payload_size = int(max_payload_size)

            # if the server can not recive any data
            if not max_payload_size:
                print("Server can not recive any data.\n"
                      f"The maximum payload size that the server can handle is {max_payload_size}.\n"
                      "Exiting...")
                sys.exit(1)
            print(f"Max payload size: {max_payload_size}")
        except ConnectionRefusedError:
            print("Error: Connection was refused by the server.")
            sys.exit(1)
        except ValueError:
            print("Error: Could not convert data to an integer.")
            sys.exit(1)

        # Implement the RDT protocol here

        # Performs fragmentation on the message if it exceeds
        # the maximum size and returns the fragments as a bytes array
        message_fragments = split_message_into_fragments(
            message, max_payload_size)
        print(f"Sending {len(message_fragments)} fragments to the server.")
        print(f"Message fragments: \n{message_fragments}")

    pass


def split_message_into_fragments(message: str, max_payload_size: int) -> list[bytes]:
    msg_bytes = message.encode()
    msg_len = len(msg_bytes)
    if msg_len <= max_payload_size:
        return [msg_bytes]
    else:
        fragments = [msg_bytes[i:i + max_payload_size]
                     for i in range(0, msg_len, max_payload_size)]
        return fragments


if "__main__" == __name__:

    parser = argparse.ArgumentParser(
        description="Client for the Reliable Data Transfer Protocol")

    parser.add_argument('-p', '--port', type=int,
                        default=DEFAULT_SERVER_PORT, help='Port number to connect to')
    parser.add_argument('-a', '--address', type=str,
                        default=DEFAULT_SERVER_HOST, help='IP Address to connect to')
    parser.add_argument('-f', '--file', type=str, default=None, help='''
                        The file that implements the required format
                        and contains the message, sliding window size,
                        and timeout value. 
                        Format example:
                        message:"This is a test message" 
                        maximum_msg_size:400 
                        window_size:4 
                        timeout:5
                        ''')

    args = parser.parse_args()

    if args.file:
        message, window_size, timeout = handle_file_input(args.file)
    else:
        message, window_size, timeout = handle_user_input()

    print(
        f"Message: {message}, Window Size: {window_size}, Timeout: {timeout}")

    start_transmission(args.address, args.port, message, window_size, timeout)

    pass
