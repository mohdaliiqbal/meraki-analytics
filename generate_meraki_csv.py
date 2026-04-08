#!/usr/bin/env python3
"""
Generate realistic Meraki network metrics CSV data.
Usage:
    python generate_meraki_csv.py                        # defaults: 10,000 rows, output meraki_metrics.csv
    python generate_meraki_csv.py --rows 50000           # custom row count
    python generate_meraki_csv.py --rows 1000 --out data.csv
"""

import csv
import random
import argparse
from datetime import datetime, timedelta, timezone

# ── Meraki-realistic reference data ──────────────────────────────────────────

CUSTOMERS = [
    "Woolworths Group",
    "Commonwealth Bank",
    "Telstra",
    "JB Hi-Fi",
    "Bunnings Warehouse",
    "ANZ Banking Group",
    "Wesfarmers",
    "Medibank",
    "Transurban",
    "Virgin Australia",
]

NETWORK_TEMPLATES = {
    "Woolworths Group":      ["WOW-NSW-CORP", "WOW-VIC-RETAIL", "WOW-QLD-DC"],
    "Commonwealth Bank":     ["CBA-SYDNEY-HQ", "CBA-MELB-BRANCH", "CBA-PERTH-BRANCH"],
    "Telstra":               ["TEL-CORE-SYD", "TEL-EDGE-MEL", "TEL-EDGE-BNE"],
    "JB Hi-Fi":              ["JBHIFI-MELB-STORE", "JBHIFI-SYD-STORE", "JBHIFI-CORP"],
    "Bunnings Warehouse":    ["BWH-VIC-STORE01", "BWH-NSW-STORE02", "BWH-QLD-STORE03"],
    "ANZ Banking Group":     ["ANZ-CBD-HQ", "ANZ-PARRAMATTA", "ANZ-DOCKLANDS"],
    "Wesfarmers":            ["WES-PERTH-HQ", "WES-SYD-OFFICE", "WES-MEL-OFFICE"],
    "Medibank":              ["MED-MELB-HQ", "MED-SYD-BRANCH"],
    "Transurban":            ["TCL-MEL-NOC", "TCL-SYD-NOC"],
    "Virgin Australia":      ["VAU-BNE-HQ", "VAU-SYD-OPS", "VAU-MEL-OPS"],
}

# Meraki device naming convention: MX = security appliance, MS = switch, MR = AP
DEVICE_TEMPLATES = [
    ("MX250", "security_appliance"),
    ("MX105", "security_appliance"),
    ("MX68",  "security_appliance"),
    ("MS390", "switch"),
    ("MS225", "switch"),
    ("MS120", "switch"),
    ("MR56",  "access_point"),
    ("MR44",  "access_point"),
    ("MR36",  "access_point"),
]

# Realistic interface names per device type
INTERFACES = {
    "security_appliance": ["WAN1", "WAN2", "LAN", "DMZ", "VPN-Tunnel-0", "VPN-Tunnel-1"],
    "switch":             ["Port-1", "Port-2", "Port-3", "Port-4", "Port-48", "Uplink-1", "Uplink-2"],
    "access_point":       ["radio0", "radio1", "eth0"],
}

METRIC_NAMES = [
    "uplink.kbps",
    "downlink.kbps",
    "usage.kbps",
    "latency.kbps",        # treated as throughput proxy in Meraki API
    "throughput.kbps",
    "wireless.usage.kbps",
    "client.usage.kbps",
]

# Typical kbps ranges per interface type
KBPS_RANGES = {
    "WAN1":         (5_000,  900_000),
    "WAN2":         (1_000,  500_000),
    "LAN":          (10_000, 950_000),
    "DMZ":          (500,    50_000),
    "VPN-Tunnel-0": (1_000,  200_000),
    "VPN-Tunnel-1": (1_000,  200_000),
    "Uplink-1":     (10_000, 950_000),
    "Uplink-2":     (10_000, 950_000),
    "radio0":       (1_000,  300_000),
    "radio1":       (1_000,  300_000),
    "eth0":         (5_000,  100_000),
}

def get_kbps(interface_name: str) -> float:
    lo, hi = KBPS_RANGES.get(interface_name, (100, 100_000))
    # Add a bit of realistic noise / occasional spikes
    base = random.uniform(lo, hi)
    if random.random() < 0.05:      # 5% chance of a spike
        base = min(base * random.uniform(2, 5), hi * 1.2)
    return round(base, 2)

def build_device_pool(network: str, n: int = 5):
    """Create a fixed pool of devices for a network (consistent naming)."""
    pool = []
    for i in range(n):
        model, dtype = random.choice(DEVICE_TEMPLATES)
        serial = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=4))
        name = f"{network.split('-')[0]}-{model}-{serial}"
        ifaces = INTERFACES[dtype]
        pool.append((name, dtype, ifaces))
    return pool

def generate_rows(num_rows: int):
    # Pre-build device pools per network for consistency
    device_pools = {}
    for customer, networks in NETWORK_TEMPLATES.items():
        for net in networks:
            device_pools[net] = build_device_pool(net)

    # Start timestamps spread over the last 30 days
    end_ts   = datetime.now(timezone.utc)
    start_ts = end_ts - timedelta(days=30)
    span_sec = int((end_ts - start_ts).total_seconds())

    rows = []
    for _ in range(num_rows):
        customer = random.choice(CUSTOMERS)
        network  = random.choice(NETWORK_TEMPLATES[customer])
        device_name, _, ifaces = random.choice(device_pools[network])
        interface = random.choice(ifaces)
        metric    = random.choice(METRIC_NAMES)
        kbps      = get_kbps(interface)
        ts        = start_ts + timedelta(seconds=random.randint(0, span_sec))

        rows.append({
            "timestamp":     ts.strftime("%Y-%m-%d %H:%M:%S"),
            "customer":      customer,
            "networkName":   network,
            "deviceName":    device_name,
            "interfaceName": interface,
            "kbps":          kbps,
            "metricName":    metric,
        })

    # Sort by timestamp for realism
    rows.sort(key=lambda r: r["timestamp"])
    return rows

def main():
    parser = argparse.ArgumentParser(description="Generate Meraki network metrics CSV")
    parser.add_argument("--rows", type=int, default=10_000, help="Number of rows (default: 10000)")
    parser.add_argument("--out",  type=str, default="meraki_metrics.csv", help="Output filename")
    args = parser.parse_args()

    print(f"Generating {args.rows:,} rows → {args.out} ...")
    rows = generate_rows(args.rows)

    fieldnames = ["timestamp", "customer", "networkName", "deviceName", "interfaceName", "kbps", "metricName"]
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! {len(rows):,} rows written to {args.out}")
    print(f"\nSample (first 3 rows):")
    for row in rows[:3]:
        print(" ", row)

if __name__ == "__main__":
    main()