import sys
import csv
import time
import socket
import threading

def node_logger(sock, addr):
    count = 0
    node_name = ''
    while True:
        count += 1
        data = sock.recv(1024)
        recv_time = time.time() # record receive time immediately after receiving the msg
        log_timestamp.append((recv_time, len(data))) # list appending is thread-safe in python
        msg = data.decode('utf-8').split()

        # node disconnected
        if not data or data.decode('utf-8') == 'exit':
            print("%s - %s disconnected" % (recv_time, node_name))
            break

        # unknown message
        if len(msg) != 3:
            print("Wrongly formatted message from node %s")
            continue

        node_name = msg[0]
        msg_time = msg[1]
        msg_text = msg[2]

        # connect for the first time, print connection info
        if count == 1:
            print("%s - %s connected" % (recv_time, node_name))
        # print message from the node
        print("%s %s" % (msg_time, node_name))
        print(msg_text)

        # obtain delay
        delay = recv_time - float(msg_time)
        # obtain bandwidth
        nbyte = 0
        lock.acquire()
        try:
            for i in range(len(log_timestamp)):
                if log_timestamp[-i-1][0] < recv_time:
                    break
                nbyte += log_timestamp[-i-1][1]
        finally:
            lock.release()
        bandwidth = nbyte/delay
        # record log metrics
        w.writerow([node_name, delay, bandwidth])
    sock.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        logger_port = int(sys.argv[1])
    else:
        logger_port = 1234

    with open("log_metric.csv", mode="w") as files:        
        w = csv.writer(files)
        w.writerow(['Node','Delay [sec]', 'Bandwidth [bytes/sec]'])

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', logger_port))
        s.listen(10)

        lock = threading.Lock()
        log_timestamp = []

        while True:
            sock, addr = s.accept()
            t = threading.Thread(target=node_logger, args=(sock, addr))
            t.start()
