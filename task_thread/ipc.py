"""ipc.py : Intercom using system pipes with special interest in intercom between 
async and normal processes

* Copyright: 2022 Sampsa Riikonen
* Authors  : Sampsa Riikonen
* Date     : 1/2022
* Version  : 0.0.2

This file is part of the task_thread library

Licensed according to the MIT License.  Please see file COPYING.MIT for more details.
"""
import os, pickle, math


class Duplex:

    def __init__(self, read_fd, write_fd):
        # file descriptors, i.e. numbers:
        self.read_fd = read_fd
        self.write_fd = write_fd
        # these are _io.FileIO objects:
        self.reader = os.fdopen(read_fd, "br", buffering = 0)
        self.writer = os.fdopen(write_fd, "bw", buffering = 0)
    
    def getReadIO(self):
        """_io.FileIO object
        """
        return self.reader

    def getReadFd(self):
        return self.read_fd

    def getWriteFd(self):
        return self.write_fd

    def getWriteIO(self):
        """_io.FileIO object
        """
        return self.writer

    def recv(self):
        """Traditional blocking recv
        """
        msg = b''
        N = None
        cc = 0
        while True:
            # print("waiting stream")
            res = self.reader.read(8)
            cc += 8
            if N is None:
                # decode the first 8 bytes into int
                N = int.from_bytes(res, byteorder = "big")
                # print("N>", N)
            # print(res, len(res))
            msg += res
            if cc >= N:
                break
        msg = msg[8:N] # remove any padding bytes
        obj = pickle.loads(msg)
        return obj

    def send(self, obj):
        """Tradition blocking send
        """
        msg = to8ByteMessage(obj)
        n = self.writer.write(msg)
        # self.writer.flush() # no effect
        # print("wrote", n, "bytes")
        return n

    def __del__(self):
        self.reader.close()
        self.writer.close()


def getPipes(block_A = False, block_B = False):
    """

    Either A or B can be blocking or non-blocking 

    non-blocking pipe-terminal is required for asyncio

    ::

        A           B

        w --------> r
        r <-------- w

        (A_w, A_r) is returned as single duplex
    """
    B_read_fd, A_write_fd = os.pipe()
    A_read_fd, B_write_fd = os.pipe()
    #print("read, write pair", B_read_fd, A_write_fd)
    #print("read, write pair", A_read_fd, B_write_fd)
    # these a file descriptors, i.e. numbers

    if block_A:
        os.set_blocking(A_read_fd, True)
        os.set_blocking(A_write_fd, True)
    else:
        os.set_blocking(A_read_fd, False)
        os.set_blocking(A_write_fd, False)

    if block_B:
        os.set_blocking(B_read_fd, True)
        os.set_blocking(B_write_fd, True)
    else:
        os.set_blocking(B_read_fd, False)
        os.set_blocking(B_write_fd, False)

    return Duplex(A_read_fd, A_write_fd), Duplex(B_read_fd, B_write_fd)


def to8ByteMessage(obj):
    b = pickle.dumps(obj)
    # r, w, e = safe_select([], [self.write_fd], [])
    # print("writing to", self.write_fd)
    val = len(b) + 8 # length of the message, including the first 8 bytes
    lenbytes = val.to_bytes(8, byteorder = "big")
    n_pad = math.ceil(val/8)*8 - val
    pad = bytes(n_pad)
    return lenbytes + b + pad

