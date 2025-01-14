# Communication Networks Assignment 3 - Reliable Ordered Data Transfer Protocol Simulation

## Description
This repository contains a Python implementation of a simplified reliable, ordered data transfer protocol inspired by TCP. The system uses a client-server model and incorporates essential mechanisms for reliable data transfer
such as segmentation, sliding windows, acknowledgments, and timeout-based retransmissions.


## Features
- **Message Segmentation**: Splits data into chunks according to a server-defined limit.
- **Sliding Window Protocol**: Allows for controlled, efficient data transfer with a fixed window size.
- **Acknowledgment Mechanism**: Ensures the server confirms the receipt of contiguous packets.
- **Timeout and Retransmission**: Resends unacknowledged packets after a specified timeout.


## Project Structure
- **`client.py`**: Implements the client logic for data segmentation, sliding windows, and retransmissions.
- **`server.py`**: Handles incoming data, acknowledges received packets, and ensures ordered delivery.
- **`packet.py`**: Defines the `Packet` class, which encapsulates packet structure and serialization.
- **`input.txt`**: An example of a valid text file that can be received as input by the client and the server.
- **`assignment_requirements.txt`**: Original assignment requirements documentation.


## Usage
### Running the Server
```bash
python server.py [-a <IP_ADDRESS>] [-p <PORT>] [-f <CONFIG_FILE>]
```
- `-a`: Specify the IP address to bind the server (Default is '127.0.0.1').
- `-p`: Specify the port number to bind the server (Default is 9999).
- `-f`: Optional configuration file with `maximum_msg_size`.

### Running the Client
```bash
python client.py [-a <SERVER_IP>] [-p <SERVER_PORT>] [-f <CONFIG_FILE>]
```
- `-a`: Specify the server's IP address (Default is '127.0.0.1').
- `-p`: Specify the server's port number (Default is 9999).
- `-f`: Optional configuration file with message, window size, and timeout.


## Configuration File Format
```plaintext
message: "<Your Message>"
maximum_msg_size: <Max Bytes>
window_size: <Window Size>
timeout: <Timeout in Seconds>
```
Example:
```plaintext
message: "This is a test message"
maximum_msg_size: 400
window_size: 4
timeout: 5
```


## Key Concepts
1. **Reliability**: Ensures data is delivered in order, without loss, through acknowledgment and retransmission mechanisms.
2. **Efficiency**: Employs a sliding window protocol to balance throughput and resource usage.
3. **Customization**: Configurable parameters for flexible operation.


## Requirements
- Python 3.x


