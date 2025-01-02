import sys
import socket
import threading
import time
import argparse

DEFAULT_SERVER_HOST = '127.0.0.1'
DEFAULT_SERVER_PORT = 9999


def handle_file_input(file_path: str) -> tuple[str, int, int, int]:
    try:
        with open(file_path, 'r') as file:
            data = file.read().split('\n')
            message = data[0].split(':')[1].strip().strip('"')
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


def handle_user_input() -> tuple[str, int, int, int]:
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

    pass


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

    pass
