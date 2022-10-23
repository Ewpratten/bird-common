import argparse
from pathlib import Path
import socket
import sys
from typing import List

def dump_all_aspaths(bird_socket_path: Path) -> List[List[int]]:
    
    # Open the unix socket
    bird_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bird_socket.connect(bird_socket_path.as_posix())

    # Send the command to dump all paths
    bird_socket.sendall(b"show route all\r\n")
    
    # Read the response until there is no more data
    while True:
        data = bird_socket.recv(4096)
        if not data:
            break
        
        # Process each line
        for line in data.decode("utf-8").splitlines():
        
            # Skip lines without aspath info
            if "BGP.as_path" not in line:
                continue
            
            print(line)

def main() -> int:
    # Handle program arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-s","--socket", help="Path to the birdctl unix socket", default="/var/run/bird/bird.ctl")
    args = ap.parse_args()
    
    dump_all_aspaths(Path(args.socket))

    return 0

if __name__ == "__main__":
    sys.exit(main())