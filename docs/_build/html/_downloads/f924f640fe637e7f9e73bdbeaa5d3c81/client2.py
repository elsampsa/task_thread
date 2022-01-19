import socket, time, json

INT_NBYTES = 4

def autoReadSock(sock):
    """Read first message length, then the message
    """
    len_bytes = bytes()
    left = INT_NBYTES
    while left > 0:
        len_bytes += sock.recv(left)
        if len(len_bytes) < 1:
            return None
        left -= len(len_bytes)

    left = int.from_bytes(len_bytes, "big")
    msg_bytes = bytes()
    while left > 0:
        msg_bytes_ = sock.recv(4096)
        if len(msg_bytes_) < 1:
            return None
        else:
            msg_bytes += msg_bytes_
            left -= len(msg_bytes_)
    return msg_bytes


def bytes2Payload(bytes_):
    bytes_ = len(bytes_).to_bytes(INT_NBYTES, "big") + bytes_
    return bytes_


def sendAll(sock = None, bytes_ = None, mbps = 1):
    kbps = mbps * 1024
    bytes_per_second = 1024*kbps/8
    seconds_per_byte = 1/bytes_per_second
    block_size = 1500 # standard mtu size
    f=block_size*8/1000 # one block in kb
    cc = len(bytes_) // block_size
    to = 0

    for i in range(cc):
        fr = i*block_size
        to = (i+1)*block_size
        blob_ = bytes_[fr:to]
        # print("sending:", fr, to, np.frombuffer(blob_, dtype=np.uint8)[0:10])
        t=time.time()
        sock.sendall(
            blob_
        )
        dt=time.time()-t
        kbps_ = f/dt
        delay=max(seconds_per_byte*block_size-dt,0)
        time.sleep(delay) # delay to reach target kbps

    if to < len(bytes_):
        blob_ = bytes_[to:]
        # print("sending rest:",to, np.frombuffer(blob_, dtype=np.uint8)[0:10])
        t=time.time()
        sock.sendall(
            blob_
        )
        dt=time.time()-t
        delay=max(seconds_per_byte*block_size-dt,0)
        time.sleep(delay) # delay to reach target kbps


def sendAllBytes(sock = None, bytes_ = None, mbps = 1):
    bytes_ = bytes2Payload(bytes_)
    sendAll(sock = sock, bytes_ = bytes_, mbps = mbps)


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("localhost", 5002))
b = autoReadSock(sock)
dic = json.loads(b.decode("utf-8"))
print("got from server:", dic)
mbps = 1000
n=22; print("sending payload"); sendAllBytes(sock=sock, bytes_=bytes(n), mbps=mbps)
n=68; print("sending payload"); sendAllBytes(sock=sock, bytes_=bytes(n), mbps=mbps)
n=1024; print("sending payload"); sendAllBytes(sock=sock, bytes_=bytes(n), mbps=mbps)
for i in range(50):
    n=1024*1024; print("sending payload", i); sendAllBytes(sock=sock, bytes_=bytes(n), mbps=mbps)
sock.close()
