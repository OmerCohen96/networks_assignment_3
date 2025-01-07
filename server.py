import argparse
import socket
import sys
import threading
import time
from packet import Packet


DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 9999
CLIENT_BUFFER_SIZE = 1024
# The maximum message size that can be received by the server
# This value will be set by the user or read from the file
MAX_MSG_SIZE = 0


def handle_acknowledgement(packets: list[Packet], packet: Packet) -> int:
    """
    Handles the acknowledgment of the received packets and returns the last acknowledged packet number
    Also organizes the received packets in the correct order in the packets list.

    This function processes the received packet by updating the list of packets with the new packet.
    It ensures that packets are stored in the correct order and fills in any gaps with None values.
    The function then returns the highest contiguous sequence number of packets that have been received.
    """
    # Extract the sequence number from the packet
    seq_num = packet.seq_num
    packets_len = len(packets)

    # If the sequence number is equal to the length of the packets list
    # It's means that the packet received is the next packet in the order after the last packet
    # So, append the packet to the next index in the list
    if seq_num == packets_len:
        packets.append(packet)

    # If the sequence number is greater than the length of the packets list
    # It's means that there are missing packets between the last packet and the received packet
    # So extend the list with None values and then append the packet
    # The none values indicate which packets are missing
    elif seq_num > packets_len:
        packets.extend([None for _ in range((seq_num - packets_len))])
        packets.append(packet)

    # The sequence number of the recievd packet is less than the length of the packets list
    # If the list at the sequence number is None, it's means that the packet is not received yet
    # And the packet should be added to the list
    # Otherwise, the packet is already received and no need to add it again
    elif packets[seq_num] is None:
        packets[seq_num] = packet

    # Check if there are any missing packets
    # If there are missing packets, return the index of the last packet in the sequence
    # Otherwise, return the length of the packets list - 1 (The last packet in the sequence)
    for i, pkt in enumerate(packets):
        if pkt is None:
            return i - 1
    return len(packets) - 1


def handle_client(client_socket: socket.socket, addr: tuple[str, int]):
    """
    Handles the communication with a connected client.

    This function is responsible for managing the communication with a client that has connected
    to the server. It sends the maximum message size to the client, receives packets from the client,
    processes the packets, and sends acknowledgments back to the client. The function runs in a loop
    until the client disconnects or an error occurs.

    """
    with client_socket:
        print(f"Connected to {addr}")

        # Send the max message size to the client
        maximum_message_size = str(MAX_MSG_SIZE).encode()

        # Pad the message to the client buffer size
        # to ensure that the message is sent correctly
        maximum_message_size = maximum_message_size + b' ' * \
            (CLIENT_BUFFER_SIZE - len(maximum_message_size))

        client_socket.sendall(maximum_message_size)

        # List to store all received packets
        # This list will be used to reconstruct the message
        packets = []

        while True:
            try:
                # Receive the packets from the client
                # Limit the received data to the maximum message size + the packet header size
                data = client_socket.recv(MAX_MSG_SIZE + Packet.HEADER_SIZE)
                if not data:
                    break
                # Unpack the received data
                packet = Packet.unpack(data)

                # This function handles the acknowledgment of the received packets
                # and returns the last acknowledged packet number
                # Also, it organizes the received packets in the correct order in the packets list
                ack_number = handle_acknowledgement(packets, packet)
                print(f"ack: {ack_number} of the last packet in the sequence")

                # Send the correct acknowledgment number back to the client
                if ack_number >= 0:
                    ack_packet = Packet(ack_number, ack_msg=True)
                    client_socket.sendall(ack_packet.pack())
                    print(f"Acknowledgment sent for packet {ack_number}")

                # If in the recievd packet the ack_msg flag is set, its means that the client
                # Received acknowledgment for the last packet in the sequence
                # and the server should stop receiving packets
                # So, break the loop and close the connection
                if packet.ack_msg == True:
                    print("Last packet received.")
                    time.sleep(1)
                    break
            except socket.error as e:
                print(f"Error occurred with the socket in handle_client: {e}")
                break
            except Exception as e:
                print(f"Error occurred in handle_client: {e}")
                break

        # after the loop ends, check if there are any missing packets
        if not packets or None in packets:
            print("Error: Some packets are missing.")

        # Combine the packets data and gather the complete message
        message_bytes = b''.join(list(map(lambda x: x.data, packets)))
        message = message_bytes.decode()
        print(f"Message received: {message}")

        print(f"Closing connection with {addr}...")


def initialize_server_socket(address: str, port: int):

    # Create a server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        try:
            # Bind the server socket to the address and port
            server_socket.bind((address, port))
            server_socket.listen()
            print(f"Server is listening on {address}:{port}")

            # # Set timeout for the server socket
            server_socket.settimeout(35)

            threads = []

            print("Waiting for a connections...")

            while True:
                # Accept the client connection
                client_socket, addr = server_socket.accept()

                # Create a new thread to handle the client
                t = threading.Thread(target=handle_client,
                                     args=(client_socket, addr))
                t.start()
                threads.append(t)

        except socket.timeout:
            print("Connection timed out.")
        except socket.error as e:
            print(f"Error in initialize_server_socket: {e}")
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
        print("Error: Invalid input. Please enter valid integer as string.")
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

    MAX_MSG_SIZE = maximum_msg_size
    print("Initializing server...")
    initialize_server_socket(args.address, args.port)

    # End point of the program
    print("Server has been closed.")
