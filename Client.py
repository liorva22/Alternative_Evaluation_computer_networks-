import random
import struct
import socket


class TriviaClient:
    def __init__(self, udp_port=13117):
        self.udp_port = udp_port
        self.server_address = None
        self.tcp_port = None
        self.nickname = "Player" + str(random.randint(1, 9999))

    def listen_for_offers(self):
        print("Client started, listening for offer requests...")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', self.udp_port))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            while True:
                data, addr = sock.recvfrom(1024)
                try:
                    # Adjust the unpack format to include the server name
                    magic_cookie, message_type, server_name_packed, tcp_port = struct.unpack('!Ib32sH', data)
                    if magic_cookie == 0xabcddcba and message_type == 0x2:
                        # Decode the server name, ensuring to strip null bytes
                        server_name = server_name_packed.decode('utf-8').rstrip('\x00')
                        self.server_address = addr[0]
                        self.tcp_port = tcp_port
                        print(
                            f"Received offer from server \"{server_name}\" at address {self.server_address}, attempting to connect...")
                        return
                except struct.error:
                    continue

    def connect_to_server(self):
        if self.server_address is None or self.tcp_port is None:
            print("No server to connect to.")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((self.server_address, self.tcp_port))
            print(f"Connected to server {self.server_address}:{self.tcp_port}.")  # debug
            tcp_socket.sendall(f"{self.nickname}\n".encode())

            self.game_mode(tcp_socket)

    # def game_mode(self, tcp_socket):
    #     print("Entered game mode. Waiting for questions and your answers...")
    #
    #     while True:
    #         # Check for incoming data from server
    #         try:
    #             tcp_socket.setblocking(False)  # Set socket to non-blocking mode
    #             data = tcp_socket.recv(1024).decode().strip()
    #             if data:
    #                 print(data)
    #         except BlockingIOError:
    #             pass  # No data available
    #         except Exception as e:
    #             print(f"Error receiving data: {e}")
    #             break
    #
    #         # Check for keyboard input
    #         if msvcrt.kbhit():
    #             char = msvcrt.getch().decode()  # Get the character pressed
    #             print(f"You pressed: {char}")  # Echo the character back to the user
    #             try:
    #                 tcp_socket.sendall(char.encode())  # Send the character to the server
    #             except Exception as e:
    #                 print(f"Error sending data: {e}")
    #                 break
    #
    #         # You may want to introduce a slight delay to reduce CPU usage in this loop
    #         time.sleep(0.1)

    def game_mode(self, tcp_socket):
        print("I'm in. Waiting for the question...")  # debug
        while True:
            try:
                tcp_socket.setblocking(True)  # Set the socket to blocking mode to wait for the question
                data = tcp_socket.recv(1024).decode().strip()
                if data:
                    print(data)
                    if "True or False" in data:  # If the question is received, wait for user input
                        answer = input("Your answer (Y/N): ").strip().upper()
                        tcp_socket.sendall(answer.encode())
                        # Receive and print the validation result from the server
                        validation_result = tcp_socket.recv(1024).decode().strip()
                        print(validation_result)

            except Exception as e:
                print(f"Error during game: {e}")
                break

    def run(self):
        self.listen_for_offers()
        self.connect_to_server()


if __name__ == "__main__":
    client = TriviaClient()
    client.run()
