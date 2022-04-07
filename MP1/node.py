from ast import Try
import sys 
import socket
import threading

from sympy import true

# print(sys.argv)

class Message:
    def __init__(self):
        self.SenderNodeName = ""
        self.Content = ""
        self.MessageID = ""   # id = node name + message timestamp when sending
        self.priority = (0, "")  # the priority
        self.deliverable = False

    def __init__(self, msg_str):
        msg_list = msg_str.split('|')
        self.SenderNodeName = msg_list[0]
        self.Content = msg_list[1]
        self.MessageID = msg_list[2]
        self.priority = (msg_list[3], msg_list[0])
        self.deliverable = False

    def get_message_string(self):
        # convert the class to string message so that you can send via network
        return "%s|%s|%s|%s" %(self.SenderNodeName, self.Content, self.MessageID, self.priority)

def msg_sort_key(msg):
    return msg.priority

class ISISQueue:
    def __init__(self):
        self.queue = []
        self.feedback_table = dict()

    def sort(self):
        self.queue.sort(key=msg_sort_key, reverse=True)

    def append(self, msg):
        self.queue.append(msg)
        self.feedback_table[msg.MessageID] = [1, (0, "")] # [receiving time, max priority]
        self.sort()

    def delete(self, msg_id):
        for msg in self.queue:
            if msg.MessageID == msg_id:
                self.queue.remove(msg)
                self.feedback_table.pop(msg_id)
        self.sort()

    def deliver(self):
        delivered_msg = []
        while len(self.queue) != 0 and self.queue[-1].deliverable:
            self.feedback_table.pop(self.queue[-1].MessageID)
            delivered_msg.append(self.queue.pop(-1))
        return delivered_msg

    # deliver used when failure happens
    def deliver_fail(self, node_name):
        delivered_msg = []
        while len(self.queue) != 0 and self.queue[-1].:
            self.feedback_table.pop(self.queue[-1].MessageID)
            delivered_msg.append(self.queue.pop(-1))
        return delivered_msg

    def update_priority(self, new_msg, node_num, node_name):
        agreed_priority = -1
        l = self.feedback_table[new_msg.MessageID]
        l[0] += 1 # update receiving time
        # if it is feedback info
        if msg.SenderNodeName == node_name:
            l[1] = max(l[1], new_msg.priority)
        # if it is the agreed priority (receiving time == number of nodes)
        if l[0] == len(node_num) + 1:
            for msg in self.queue:
                if msg.MessageID == new_msg.MessageID:
                    msg.priority = max(l[1], msg.priority)
                    agreed_priority = msg.priority
                    msg.deliverable = True
                    self.sort()
                    break
        return agreed_priority


isis_q = ISISQueue()
seen_msg = set()
send_socket = dict()
receive_socket = dict()
prop_priority = 0

isis_q_lock = threading.Lock()
seen_msg_lock = threading.Lock()
send_socket_lock = threading.Lock()
receive_socket_lock = threading.Lock()
prop_priority_lock = threading.Lock()


def receive_message(s, node_name):
    # write code to wait until all the nodes are connected
    while True:
        try:
            # use socket recv and than decode the message (eg. utf-8)
            msg = Message(s.recv().decode('utf-8'))
            # based on whether I have seen this message
            if msg in seen_msg:
                # if I have seen the message, I could either be
                #   sender who get the feedback from other nodes or
                #   receiver who get msg from other nodes' R-multicast
                # But no matter whether I am sender or receiver, I will meet a msg n times, (n is the number of the node)
                # and I will get the agreed priority of this msg when I meet the msg at nth time
                isis_q_lock.acquire()
                receive_socket_lock.acquire()
                agreed_priority = isis_q.update_priority(msg, len(receive_socket), node_name)
                receive_socket_lock.release()
                if agreed_priority != -1:
                    deliver()
                prop_priority_lock.acquire()
                prop_priority = max(prop_priority, agreed_priority)
                prop_priority_lock.release()
                isis_q_lock.release()
            else:
                # if I have never seen this message, then I am not the sender,
                # I will deliver it and then multicast it
                # then every process knows my proposed priority, then can decide their own agreed priority for this message
                prop_priority_lock.acquire()
                prop_priority += 1
                msg.priority[0] = (prop_priority, node_name)
                prop_priority_lock.release()
                seen_msg.add(msg)
                isis_q_lock.acquire()
                isis_q.append(msg)
                isis_q_lock.release()
                multicast(msg)
        except:
            receive_socket.pop(s)
            s.close()
            break

def get_events(node_name):
    # write code to wait until all the nodes are connected 
    for line in sys.stdin:
        # init the message struct
        msg = Message()
        msg.SenderNodeName = node_name
        msg.Content = line
        msg.MessageID = node_name
        prop_priority_lock.acquire()
        prop_priority += 1
        msg.priority = (prop_priority, node_name)
        prop_priority_lock.release()
        # register this message to some data structure to show that I have seen this message
        seen_msg_lock.acquire()
        seen_msg.add(msg)
        seen_msg_lock.release()
        isis_q_lock.acquire()
        isis_q.append(msg)
        isis_q_lock.release()
        multicast(msg)

def update_balances(queue_head_message):
    # TODO
    # some code
    print_balances()
    pass

def deliver():
    delivered_msg = isis_q.deliver()
    if len(delivered_msg) == 0:
        return
    for msg in delivered_msg:
        update_balances(msg.Content)

def multicast(msg):
    for n in send_socket:
        # send message, check if it has error
        s = send_socket[n]
        res = s.send(msg.get_message_string().encode("utf-8"))
        if not res:
            # delete this connection
            send_socket_lock.acquire()
            send_socket.pop(n)
            send_socket_lock.release()
            # close this socket
            n.close()
            # run deliver_queue_head() because a node is dead, maybe the queue's head don't have to wait for feedback
            # TODO
            deliver_queue_head()

def deliver_queue_head():
    # # check if the head of the queue has the reply from all the messages
    # # eg. 
    # if num_delivered(queue.head()) == len(connection_list) + 1: # +1 mean self delivery
    #     update_balances(queue.head())
    #     # delete that message from queue 
    pass

def node_connect(id, addr, port):
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((addr, port))
            send_socket_lock.acquire()
            send_socket[id] = s
            send_socket_lock.release()
        except:
            continue

def read_config(filename):
    f = open(filename, "r")
    node_num = int(f.readline().strip())
    node_info = []
    for line in f:
        info = line.strip().split()
        info[2] = int(info[2])
        node_info.append(info)
    return node_num, node_info

def main():
    if len(sys.argv) != 4:
        print('Incorrect input arguments')
        sys.exit(0)
    node_name = sys.argv[1]
    port = int(sys.argv[2])
    host = '127.0.0.1' # can connect with any ip
    config_fname = sys.argv[3]

    # read condig information from file
    node_num, node_info = read_config(config_fname)

    # connect other nodes
    for info in node_info:
        connect_t = threading.Thread(target=node_connect, args=(info[0], info[1], info[2]))
        connect_t.start()

    # listen other nodes
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(64)
    while len(receive_socket) != node_num:
        sock, addr = s.accept()
        receive_socket.append(sock)

    # check whether all nodes are connected
    while True:
        send_socket_lock.acquire()
        if len(send_socket) == node_num:
            send_socket_lock.release()
            break
        send_socket_lock.release()

    # start receiving message
    for ss in receive_socket:
        receive_t = threading.Thread(target=receive_message, args=s)
        receive_t.start()
    
    # start sending message
    send_t = threading.Thread(target=get_events(node_name))
    send_t.start()

if __name__ == "__main__":
    main()