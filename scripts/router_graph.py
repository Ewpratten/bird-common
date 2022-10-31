import argparse
from dataclasses import dataclass
import re
import sys
import os
from pathlib import Path
import time
from typing import Dict, List, Optional
import matplotlib.pyplot as plt


@dataclass
class InterfaceIO:
    bytes_in: int
    bytes_out: int


def get_interface_io(filter: Optional[List[str]]) -> Dict[str, InterfaceIO]:

    # Dump /proc/net/dev
    with open("/proc/net/dev", "r") as f:
        lines = f.readlines()

    # Parse /proc/net/dev for interface data
    output = {}
    parse_re = re.compile(
        r"^\s*(.*):\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)", re.MULTILINE)
    for line in lines[2:]:
        matches = parse_re.match(line)

        if matches:
            interface = matches.group(1)
            bytes_in = int(matches.group(2))
            bytes_out = int(matches.group(3))

            if filter and interface not in filter:
                continue

            output[interface] = InterfaceIO(bytes_in, bytes_out)

    return output


def prune_csv_file(file: Path):

    # Only keep lines written within the last 24 hours
    print("Pruning old data")
    with open(file, "r") as f:
        lines = f.readlines()

    # Get the current timestamp
    current_timestamp = int(time.time())
    cutoff_timestamp = current_timestamp - (24 * 60 * 60)

    # Write the lines to a new file
    with open(file, "w") as f:
        for line in lines:
            if int(line.split(",")[1]) > cutoff_timestamp:
                f.write(line)


def main() -> int:
    # Handle program arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--interface", help="One or many interfaces to monitor",
                    type=str, nargs="+", required=True)
    ap.add_argument("-w", "--workdir", help="Working directory",
                    type=str, default=Path.home() / "router_graph")
    args = ap.parse_args()

    # Create directories
    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    # Get the IO data for the interfaces
    if_io_data = get_interface_io(args.interface)

    # Track the current timestamp for calculations
    current_timestamp = int(time.time())

    # Write a new csv line for each interface file
    for interface in if_io_data:
        (workdir / interface).mkdir(parents=True, exist_ok=True)
        with open(workdir / interface / "io.csv", "a") as f:
            print(f"Writing {interface} IO stats to file")
            f.write(
                f"{interface},{current_timestamp},{if_io_data[interface].bytes_in},{if_io_data[interface].bytes_out}\n")

    # Handle each interface's graphing
    for interface in args.interface:
        print(f"Processing data for: {interface}")
        prune_csv_file(workdir / interface / "io.csv")

        # Make a graph with a line for input and output
        plt.figure(figsize=(15, 7))
        plt.title(f"Interface activity for: {interface}")
        plt.xlabel("Time")
        plt.ylabel("MB/second")
        ax = plt.gca()
        ax.ticklabel_format(useOffset=False)
                
        # Collect data
        bytes_in = []
        bytes_out = []
        timestamps = []
        with open(workdir / interface / "io.csv", "r") as f:
            lines = f.readlines()
            for line in lines:
                data = line.split(",")
                bytes_in.append(int(data[2]))
                bytes_out.append(int(data[3]))
                timestamps.append(int(data[1]))
                
        # Transform the data to MB/second
        for i in range(len(bytes_in)):
            bytes_in[i] = (bytes_in[i] / (timestamps[i] - timestamps[i-1]) / 1024 / 1024) * -1
            bytes_out[i] = bytes_out[i] / (timestamps[i] - timestamps[i-1]) / 1024 / 1024
            
        # Convert the timestamps to human readable
        for i in range(len(timestamps)):
            timestamps[i] = time.strftime("%H:%M:%S", time.localtime(timestamps[i]))
            
        # Plot the data with shaded areas
        plt.plot(timestamps, bytes_in, label="Input")
        plt.plot(timestamps, bytes_out, label="Output")
        plt.fill_between(timestamps, bytes_in, 0, alpha=0.5)
        plt.fill_between(timestamps, bytes_out, 0, alpha=0.5)
        
        # Make the timestamps horizontal
        plt.xticks(rotation=90)
        
        plt.legend()
        plt.savefig(workdir / interface / "graph.png")
        plt.close()
        print(f"Wrote {workdir / interface / 'graph.png'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
