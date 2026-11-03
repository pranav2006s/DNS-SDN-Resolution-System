
import socket
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# ---------------------------------
# 1. SERVER CONFIGURATION
# ---------------------------------

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 5000
BUFFER_SIZE = 1024

# ---------------------------------
# 2. NAME-TO-IP DATABASE
# ---------------------------------

DNS_RECORDS = {
    "server1.local": "192.0.2.10",
    "server2.local": "192.0.2.20",
    "printer.local": "192.0.2.30",
    "database.local": "192.0.2.40",
    "college.local": "192.0.2.50"
}

# ---------------------------------
# 3. REQUEST HANDLER
# ---------------------------------

def handle_request(data, client_address, server_socket):

    try:
        message = data.decode("utf-8").strip()

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] "
              f"Request from {client_address}")

        print(f"Received: {message}")

        parts = message.split(maxsplit=1)

        if not parts:
            response = "ERROR Empty request"

        elif parts[0].upper() == "PING":
            response = "PONG"

        elif parts[0].upper() == "RESOLVE":

            if len(parts) != 2 or not parts[1].strip():
                response = "ERROR Hostname missing"

            else:
                hostname = parts[1].strip().lower()

                if hostname in DNS_RECORDS:
                    ip = DNS_RECORDS[hostname]
                    response = f"OK {ip}"

                    print(f"Resolved: {hostname} -> {ip}")

                else:
                    response = "NOT_FOUND"

                    print(f"Hostname not found: {hostname}")

        else:
            response = "ERROR Invalid command"

        # Send response to the requesting client
        server_socket.sendto(
            response.encode("utf-8"),
            client_address
        )

        print(f"Response sent: {response}")

    except UnicodeDecodeError:
        server_socket.sendto(
            b"ERROR Invalid encoding",
            client_address
        )

    except OSError as error:
        print(f"Socket error: {error}")


# ---------------------------------
# 4. START UDP RESOLUTION SERVER
# ---------------------------------

def start_server(host, port):

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    server_socket.bind((host, port))

    print("=" * 45)
    print("       UDP NAME RESOLUTION SERVER")
    print("=" * 45)
    print(f"Listening on: {host}:{port}")
    print(f"Available records: {len(DNS_RECORDS)}")
    print("Server is ready to receive requests...")
    print("=" * 45)

    # Thread pool allows multiple requests
    # to be processed concurrently.
    with ThreadPoolExecutor(max_workers=10) as executor:

        try:
            while True:

                data, client_address = server_socket.recvfrom(
                    BUFFER_SIZE
                )

                executor.submit(
                    handle_request,
                    data,
                    client_address,
                    server_socket
                )

        except KeyboardInterrupt:
            print("\nShutting down UDP resolver...")

        finally:
            server_socket.close()
            print("Server stopped.")


# ---------------------------------
# 5. PROGRAM ENTRY POINT
# ---------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="UDP Name Resolution Server"
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT
    )

    args = parser.parse_args()

    start_server(args.host, args.port)
