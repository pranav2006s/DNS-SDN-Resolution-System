
import socket
import time
import json
from pathlib import Path

SERVERS = [
    ("Resolver A", "127.0.0.1", 5000),
    ("Resolver B", "127.0.0.1", 5001)
]

TIMEOUT = 2
CACHE_TTL = 100

STATUS_FILE = Path(__file__).with_name("health_status.json")

cache = {}


# ---------------------------------
# READ HEALTH STATUS
# ---------------------------------

def get_server_priority():

    try:
        with open(STATUS_FILE, "r") as file:
            status = json.load(file)

        # Ignore stale health information
        if time.time() - status["updated_at"] > 15:
            raise ValueError("Health status is outdated")

        health = status["servers"]

        healthy = [
            server for server in SERVERS
            if health.get(server[0], {}).get("online", False)
        ]

        unhealthy = [
            server for server in SERVERS
            if server not in healthy
        ]

        return healthy + unhealthy

    except (OSError, ValueError, KeyError, TypeError):
        print("WARNING: Health status unavailable.")
        print("Using default resolver order.")
        return SERVERS


# ---------------------------------
# CACHE
# ---------------------------------


def check_cache(hostname):

    if hostname not in cache:
        return None

    ip, expiry = cache[hostname]

    remaining = expiry - time.monotonic()

    if remaining > 0:
        print(f"\n[CACHE HIT] Valid for {remaining:.2f} seconds")
        return ip

    print("\n[CACHE EXPIRED] Removing expired entry")

    del cache[hostname]

    return None


def store_cache(hostname, ip):

    cache[hostname] = (
        ip,
        time.monotonic() + CACHE_TTL
    )


# ---------------------------------
# RESOLUTION
# ---------------------------------

def resolve_from_servers(hostname):

    request = f"RESOLVE {hostname}"

    server_order = get_server_priority()

    print("\nResolver priority:")

    for name, ip, port in server_order:
        print(f"  {name} ({ip}:{port})")

    for name, ip, port in server_order:

        print(f"\nTrying {name} ({ip}:{port})...")

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        sock.settimeout(TIMEOUT)

        try:
            start = time.perf_counter()

            sock.sendto(
                request.encode(),
                (ip, port)
            )

            response, _ = sock.recvfrom(1024)

            latency = (
                time.perf_counter() - start
            ) * 1000

            response = response.decode().strip()

            print(f"{name} responded: {response}")
            print(f"Response time: {latency:.3f} ms")

            if response.startswith("OK "):

                resolved_ip = response[3:].strip()

                if resolved_ip:
                    print(f"Resolved using {name}")
                    return resolved_ip

            elif response == "NOT_FOUND":
                return "NOT_FOUND"

        except socket.timeout:
            print(f"{name} FAILED: Timeout")

        except OSError as error:
            print(f"{name} FAILED: {error}")

        finally:
            sock.close()

    return None


# ---------------------------------
# MAIN CLIENT
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
            break

        if not hostname:
            print("Enter a valid hostname.")
            continue

        total_start = time.perf_counter()

        cached_ip = check_cache(hostname)

        if cached_ip is not None:

            print("\n[CACHE HIT]")
            print("Hostname:", hostname)
            print("IP Address:", cached_ip)

        else:

            print("\n[CACHE MISS]")

            resolved_ip = resolve_from_servers(hostname)

            if resolved_ip == "NOT_FOUND":
                print("Hostname does not exist.")

            elif resolved_ip is None:
                print("ERROR: All resolvers unavailable.")

            else:
                print("\nResolved IP:", resolved_ip)

                store_cache(hostname, resolved_ip)

                print(f"Cached for {CACHE_TTL} seconds.")

        total_latency = (
            time.perf_counter() - total_start
        ) * 1000

        print(f"\nTotal lookup time: {total_latency:.3f} ms")


if __name__ == "__main__":
    main()
