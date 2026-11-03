
import socket
import time

# ---------------------------------
# 1. SERVER CONFIGURATION
# ---------------------------------

SERVERS = [
    ("Resolver A", "127.0.0.1", 5000),
    ("Resolver B", "127.0.0.1", 5001)
]

TIMEOUT = 2
CACHE_TTL = 100

# Cache format:
# hostname: (IP address, expiration time)

cache = {}


# ---------------------------------
# 2. CACHE LOOKUP
# ---------------------------------

def check_cache(hostname):

    if hostname not in cache:
        return None

    ip, expiry = cache[hostname]

    if time.monotonic() < expiry:
        return ip

    # Remove expired entry
    del cache[hostname]

    return None


# ---------------------------------
# 3. STORE CACHE ENTRY
# ---------------------------------

def store_cache(hostname, ip):

    expiry = time.monotonic() + CACHE_TTL

    cache[hostname] = (ip, expiry)


# ---------------------------------
# 4. QUERY RESOLUTION SERVERS
# ---------------------------------

def resolve_from_servers(hostname):

    request = f"RESOLVE {hostname}"

    for name, ip, port in SERVERS:

        print(f"\nTrying {name} ({ip}:{port})...")

        client_socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        client_socket.settimeout(TIMEOUT)

        try:
            start = time.perf_counter()

            client_socket.sendto(
                request.encode(),
                (ip, port)
            )

            response, _ = client_socket.recvfrom(1024)

            latency = (
                time.perf_counter() - start
            ) * 1000

            response = response.decode().strip()

            print(f"{name} responded: {response}")
            print(f"Server response time: {latency:.3f} ms")

            if response.startswith("OK "):

                resolved_ip = response[3:].strip()

                if not resolved_ip:
                    continue

                print(f"Resolved using {name}")

                return resolved_ip

            elif response == "NOT_FOUND":
                return "NOT_FOUND"

        except socket.timeout:
            print(f"{name} FAILED: Request timed out.")

        except ConnectionResetError:
            print(f"{name} FAILED: Connection reset.")

        except OSError as error:
            print(f"{name} FAILED: {error}")

        finally:
            client_socket.close()

    return None


# ---------------------------------
# 5. MAIN CLIENT
# ---------------------------------

def main():

    print("=" * 45)
    print("       DNS-LIKE RESOLUTION CLIENT")
    print("=" * 45)

    while True:

        hostname = input(
            "\nEnter hostname (or 'exit' to quit): "
        ).strip().lower()

        if hostname == "exit":
            print("Client shutting down.")
            break

        if not hostname:
            print("Please enter a hostname.")
            continue

        total_start = time.perf_counter()

        # First check local cache
        cached_ip = check_cache(hostname)

        if cached_ip is not None:

            print("\n[CACHE HIT]")
            print(f"Hostname: {hostname}")
            print(f"IP Address: {cached_ip}")

        else:

            print("\n[CACHE MISS]")

            resolved_ip = resolve_from_servers(hostname)

            if resolved_ip == "NOT_FOUND":
                print("Hostname does not exist.")

            elif resolved_ip is None:
                print("ERROR: All resolution servers unavailable.")

            else:

                print(f"\nResolved IP: {resolved_ip}")

                # Store successful result
                store_cache(hostname, resolved_ip)

                print(f"Cached for {CACHE_TTL} seconds.")

        total_latency = (
            time.perf_counter() - total_start
        ) * 1000

        print(f"\nTotal lookup time: {total_latency:.3f} ms")


if __name__ == "__main__":
    main()
