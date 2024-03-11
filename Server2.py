import socket
import struct
import threading
import time
from datetime import datetime, timedelta
import random

music_trivia_questions = [
    {"question": "The Beatles were originally called 'The Quarrymen'.", "is_true": True},
    {"question": "Beethoven was completely deaf by the time he was 20.", "is_true": False},
    {"question": "Elvis Presley was a black belt in karate.", "is_true": True},
    {"question": "Mozart composed over 600 works in his lifetime.", "is_true": True},
    {"question": "The song 'Happy Birthday' is in the public domain.", "is_true": True},
    {"question": "Jimi Hendrix was left-handed but played a right-handed guitar.", "is_true": True},
    {"question": "The 'British Invasion' refers to the widespread popularity of British literature in the 1960s.",
     "is_true": False},
    {"question": "A saxophone is a brass instrument.", "is_true": False},
    {"question": "The first Eurovision Song Contest was held in 1956.", "is_true": True},
    {"question": "Michael Jackson's Thriller is the best-selling album of all time.", "is_true": True},
    {"question": "Freddie Mercury was born in Zanzibar.", "is_true": True},
    {"question": "The piano has 88 keys.", "is_true": True},
    {"question": "Bob Dylan has won a Nobel Prize in Literature.", "is_true": True},
    {"question": "The original name of 'Imagine Dragons' was 'Dragon Imaginers'.", "is_true": False},
    {"question": "Vinyl records have better sound quality than CDs.", "is_true": False},
    {"question": "The world's largest concert had an attendance of over 3.5 million people.", "is_true": True},
    {"question": "Ludwig van Beethoven composed his Ninth Symphony while he was completely deaf.", "is_true": True},
    {"question": "The 'King of Pop' is a title given to Justin Bieber.", "is_true": False},
    {"question": "ABBA is an acronym formed from the first names of the band members.", "is_true": True},
    {"question": "The longest recorded flight of a chicken is 13 seconds.", "is_true": True}
]


class TriviaServer2:
    def __init__(self, tcp_port, server_ip='127.0.0.1', udp_broadcast_port=13117):
        self.tcp_port = tcp_port
        self.server_ip = server_ip
        self.udp_broadcast_port = udp_broadcast_port
        self.clients = {}  # Dictionary to store client sockets keyed by address and include player names
        self.server_name = 'TriviaMaster'.encode('utf-8')
        self.last_connection_time = datetime.now()  # Initialize with the current time
        self.start_delay = timedelta(seconds=10)
        self.game_started = False

        self.current_question = None

    def message_UDP(self):
        padded_name = self.server_name.ljust(32, b'\x00')
        message_pack = struct.pack('!Ib32sH', 0xabcddcba, 0x2, padded_name, self.tcp_port)
        return message_pack

    def udp_broadcast(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while not self.game_started:
                sock.sendto(self.message_UDP(), ('255.255.255.255', self.udp_broadcast_port))
                print("Broadcasting UDP offer...")
                time.sleep(1)

    def start_game(self):
        if not self.game_started:  # Protect against multiple starts
            self.game_started = True
            print("Game starting...")
            self.current_question = random.choice(music_trivia_questions)
            player_list = "\n".join(
                [f"Player {idx + 1}: {name}" for idx, (_, name) in enumerate(self.clients.values())])
            question_msg = self.current_question['question']
            welcome_message = f"Welcome to the {self.server_name.decode()} server, answering trivia about Music.\n{player_list}\n==\nTrue or False: {question_msg}"

            self.send_to_all_clients(welcome_message)

        # def check_answers():
        #     # Receive answers from clients and validate them
        #     correct_answer = str(self.current_question['is_true'])
        #     for client, (client_socket, _) in self.clients.items():
        #         answer = client_socket.recv(1024).decode().strip()
        #         if answer.upper() == correct_answer.upper():
        #             winner_message = f"Congratulations! You are the winner for the question: {question_msg}"
        #             client_socket.sendall(winner_message.encode())
        #             # Other clients can be informed that a winner has been declared
        #
        # threading.Timer(10, check_answers).start()

    def send_to_all_clients(self, message):
        for client_socket, _ in list(self.clients.values()):  # Use list to copy values for safe iteration
            try:
                client_socket.sendall(message.encode('utf-8'))
            except Exception as e:
                print(f"Failed to send message to a client: {e}")
                # Optional: Handle client disconnection here, if necessary

    def handle_client(self, client_socket, address):
        try:
            # Receive player name from the client
            player_name = client_socket.recv(1024).decode().strip()
            # Store client information (socket and name)
            self.clients[address] = (client_socket, player_name)
            print(f"{player_name} connected from {address}")

            # Wait for the game to start
            while not self.game_started:
                time.sleep(0.1)
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            # Optional: After the game has started, or in case of error, close client socket
            # Consideration: You might want to keep the socket open for post-game messages or multiple rounds
            client_socket.close()
            # Remove the client from the list to prevent sending messages to disconnected clients
            if address in self.clients:
                del self.clients[address]

    def accept_connections(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # Bind the server socket to the provided host and port
            server_socket.bind(('0.0.0.0', self.tcp_port))
            server_socket.listen()
            print(f"Server started, listening on IP address {self.server_ip}")

            # server_socket.settimeout(10)  # Set a timeout of 10 seconds

            # try:
            while True:  # Continuously accept new client connections
                client_socket, address = server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                client_thread.start()

                if not self.game_started:
                    if hasattr(self, 'start_timer'):
                        self.start_timer.cancel()

                    self.start_timer = threading.Timer(10, self.start_game)
                    self.start_timer.start()

            # except socket.timeout:
            #     print("No client connected within 10 seconds. Shutting down the server.")
            #     # Clean up and shut down the server
            #     server_socket.close()

    def run(self):
        threading.Thread(target=self.udp_broadcast, daemon=True).start()
        self.accept_connections()


if __name__ == "__main__":
    server = TriviaServer2(tcp_port=12345)
    server.run()
