import sys 
import socket
import threading

# print(sys.argv)

def read_config(filename):
    pass

def main():
    if len(sys.argv) != 4:
        print('Incorrect input arguments')
        sys.exit(0)
    node_name = sys.argv[1]
    port = int(sys.argv[2])
    host = '' # can connect with any ip
    config_fname = sys.argv[3]

if __name__ == "__main__":
    main()