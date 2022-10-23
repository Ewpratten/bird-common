import argparse
import socket
import sys
from typing import List

def dump_all_aspaths(bird_socket_path: str) -> List[List[int]]:
    
    # Open the unix socket
    bird_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bird_socket.connect(bird_socket_path)

    # Send the command to dump all paths
    bird_socket.sendall(b"show route all\r\n")
    
    # Read the response until there is no more data
    raw_paths: List[str] = []
    while True:
        data = bird_socket.recv(4096)
        if not data:
            break
        
        # Process each line
        for line in data.decode("utf-8").splitlines():
        
            # Skip lines without aspath info
            if "BGP.as_path" not in line:
                continue
            
            # Clean up the extra text
            aspath = line.split("BGP.as_path")[1].strip()
            raw_paths.append(aspath)
            
    # Sort and ensure the paths are unique
    raw_paths = sorted(set(raw_paths))
    
    # Parse into the final list of paths
    paths: List[List[int]] = [[int(y) for y in x.split(" ")] for x in raw_paths]
        
    return paths

def simplify_paths(paths: List[List[int]]) -> List[List[int]]:
    output = []
    for path in paths:
        
        # Keep the order, but remove duplicates
        seen = set()
        output.append([x for x in path if not (x in seen or seen.add(x))])
    
    return output

def main() -> int:
    # Handle program arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-s","--socket", help="Path to the birdctl unix socket", default="/var/run/bird/bird.ctl")
    args = ap.parse_args()
    
    all_paths = dump_all_aspaths(args.socket)
    all_paths = simplify_paths(all_paths)
    
    # Format into a graphviz dot file
    print("digraph {")
    print("  rankdir=TD;")
    for path in all_paths:
        for i in range(len(path) - 1):
            print(f"    {path[i]} -> {path[i+1]};")
    print("}")

    return 0

if __name__ == "__main__":
    sys.exit(main())