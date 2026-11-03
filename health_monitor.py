
import socket
import time
import json
import os
from pathlib import Path
from datetime import datetime

SERVERS = [
    ("Resolver A", "127.0.0.1", 5000),
    ("Resolver B", "127.0.0.1", 5001)
]

TIMEOUT = 2
CHECK_INTERVAL = 5

STATUS_FILE = Path(__file__).with_name("health_status.json")


def check_server(name, ip, port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    try:
        start = time.perf_counter()

        sock.sendto(b"PING", (ip, port))
        response, _ = sock.recvfrom(1024)

        latency = (time.perf_counter() - start) * 1000

        if response.decode().strip() == "PONG":
            return {
                "online": True,
                "latency_ms": round(latency, 3)
            }

        return {"online": False, "latency_ms": None}

    except OSError:
        return {"online": False, "latency_ms": None}

    finally:
        sock.close()


def save_status(status):

    temporary_file = STATUS_FILE.with_suffix(".tmp")

    with open(temporary_file, "w") as file:
        json.dump(status, file, indent=4)

    os.replace(temporary_file, STATUS_FILE)


def monitor():

    print("=" * 50)
    print("         RESOLVER HEALTH MONITOR")
    print("=" * 50)

    while True:

        status = {
            "updated_at": time.time(),
            "servers": {}
        }

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Checking servers...")

        for name, ip, port in SERVERS:

            result = check_server(name, ip, port)

            status["servers"][name] = result

            if result["online"]:
                print(
                    f"[ONLINE] {name} | "
                    f"Latency: {result['latency_ms']} ms"
                )
            else:
                print(f"[OFFLINE] {name}")

        save_status(status)

        print("Health status updated.")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":

    try:
        monitor()

    except KeyboardInterrupt:
        print("\nHealth monitor stopped.")
