import socket
import sys

if len(sys.argv) > 1:
    node_name = sys.argv[1]
else:
    node_name = "Default Node"

if len(sys.argv) > 2:
    logger_ip = sys.argv[2]
else:
    logger_ip = '127.0.0.1'

if len(sys.argv) > 3:
    logger_port = int(sys.argv[3])
else:
    logger_port = 1234

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("%s connected to %s" % (node_name, logger_ip))
s.connect((logger_ip, logger_port))
print("%s connected!" % (node_name))

for line in sys.stdin:
    generate_msg = line.split()
    if not generate_msg:
        break
    elif len(generate_msg) == 2:
        msg_time = generate_msg[0]
        msg_text = generate_msg[1]
    else:
        print("Wrong generated message for node %s." % (node_name))
        sys.exit()

    print("%s %s\n%s" % (msg_time, node_name, msg_text))
    s.send(("%s %s %s" %(node_name, msg_time, msg_text)).encode("utf-8"))

s.send(b'exit')
s.close()
print("%s disconnected!" % (node_name))