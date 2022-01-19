import asyncio, logging, json
import numpy as np
import traceback

from task_thread import TaskThread, reCreate, reSchedule,\
    delete, verbose, signals

INT_NBYTES = 4


def json2bytes(dic):
    """Turn dic into json bytes & append the bytes with the json bytes length
    """
    bytes_ = json.dumps(dic).encode("utf-8")
    le = len(bytes_)
    bytes_ = le.to_bytes(INT_NBYTES, "big") + bytes_
    return bytes_


class PayloadSignal(signals.Signal):
    """A generic message message signal, carrying a python object
    """
    def __init__(self, payload):
        self.payload = payload
        
    def __str__(self):
        return "<PayloadSignal with %i bytes>" % (len(self.payload))

    def getData(self):
        return self.payload



class TCPConnectionThread(TaskThread):

    def __init__(self, parent = None, reader = None, writer = None):
        super().__init__(parent = parent)
        self.reader = reader
        self.writer = writer
        self.peername, self.peerport = self.writer.get_extra_info("peername")

    def getId(self):
        return str(id(self))

    def getInfo(self):
        return "<TCPConnectionThread %s connected to %s>" % (self.getId(), self.peername)


    def initVars__(self):
        self.tasks.read_socket = None
        self.tasks.write_socket = None


    @verbose
    async def enter__(self):
        self.logger.info("enter__ : %s", self.getInfo())
        self.tasks.write_socket = await reCreate(self.tasks.write_socket, self.writeSocket__)


    @verbose
    async def exit__(self):
        self.tasks.read_socket = await delete(self.tasks.read_socket)
        self.tasks.write_socket = await delete(self.tasks.write_socket)
        self.logger.debug("exit__: bye!")


    async def readSocket__(self):
        try:
            try:
                packet = await self.reader.read(1500)
            except Exception as e:
                self.logger.warning("readSocket__ : reading failed : '%s'", e)
                self.logger.info("readSocket__: tcp connection %s terminated", self.getInfo())
                await self.terminate()
            else:
                if len(packet) > 0:
                    # all good!  keep on reading = reschedule this
                    self.logger.debug("readSocket__: got packet with size %s", len(packet))
                    # send the payload to parent:
                    await self.handlePacket__(packet)
                    self.tasks.read_socket = await reSchedule(self.readSocket__); return
                else:
                    self.logger.info("readSocket__: client at %s closed connection", self.peername)
                    await self.terminate()

        except asyncio.CancelledError:
            self.logger.info("readSocket__ : cancelling %s", self.getInfo())
            
        except Exception as e:
            self.logger.warning("readSocket__: failed with '%s'", e)
            await self.terminate()


    def resetPacketState__(self, clearbuf = False):
        self.left = INT_NBYTES
        self.len = 0
        self.header = True
        if clearbuf:
            self.buf = bytes(0)

        
    async def handlePacket__(self, packet):
        """packet reconstructions into blobs of certain length
        """
        if packet is not None:
            self.buf += packet
        if self.header:
            if len(self.buf) >= INT_NBYTES:
                self.len = int.from_bytes(self.buf[0:INT_NBYTES], "big")
                self.header = False # we got the header info (length)
                if len(self.buf) > INT_NBYTES:
                    # sort out the remaining stuff
                    await self.handlePacket__(None)
        else:
            if len(self.buf) >= (INT_NBYTES + self.len):
                # correct amount of bytes have been obtained
                payload = np.frombuffer(self.buf[INT_NBYTES:INT_NBYTES + self.len], dtype=np.uint8)
                await self.sigFromChildToParent__(PayloadSignal(
                    payload = payload))
                # prepare state for next blob
                if len(self.buf) > (INT_NBYTES + self.len):
                    # there's some leftover here for the next blob..
                    self.buf = self.buf[INT_NBYTES + self.len:]
                    self.resetPacketState__()
                    # .. so let's handle that leftover
                    await self.handlePacket__(None)
                else:
                    # blob ends exactly
                    self.resetPacketState__(clearbuf=True)
                

    async def writeSocket__(self):
        """Send one-time info message
        """
        try:
            packet = json2bytes(
                {
                    "message" : "hello!"
                })
            try:
                self.writer.write(packet)
                # await self.writer.drain() # this would maybe flush
            except Exception as e:
                self.logger.warning("writeSocket__ : writing failed : '%s'", e)
                await self.terminate()
            else:
                """sending info to the client was succesfull, let's start reading
                payload from the client"""
                self.resetPacketState__(clearbuf = True)
                self.tasks.read_socket = await reCreate(self.tasks.read_socket, self.readSocket__)

        except asyncio.CancelledError:
            self.logger.info("writeSocket__ : cancelling %s", self.getInfo())
            
        except Exception as e:
            self.logger.warning("writeSocket__: failed with '%s'", e)
            await self.terminate()


class MasterTCPServerThread(TaskThread):

    def __init__(self, parent = None, name = "thread", pause = 10, port = 5002, max_clients = 10):
        super().__init__(parent = parent)
        self.pause = pause
        self.port = port
        self.max_clients = max_clients
        self.name = name


    def initVars__(self):
        self.server = None
        self.tasks.tcp_server = None


    def getId(self):
        return str(id(self))


    def getInfo(self):
        return "<MasterTCPServerThread %s>" % (self.name)


    @verbose
    async def enter__(self):
        """Everything starts from here.  This cofunction is awaited (i.e. not scheduled as a task)
        
        - Await for something critical
        - Shedule the re-scheduling tasks
        """
        self.logger.info("entry point")
        self.tasks.tcp_server = await reCreate(self.tasks.tcp_server, self.tcpServer__)
        # now the tasks runs independently


    @verbose
    async def exit__(self):
        self.tasks.tcp_server = await delete(self.tasks.tcp_server)
        self.logger.debug("exit__: bye!")


    @verbose
    async def childsignalHandler__(self, signal, child):
        """How to handle a certain signal from children?
        """
        self.logger.debug("childsignalHandler__ : got signal %s from child %s", signal, child)
        if isinstance(signal, PayloadSignal):
            self.logger.info("Got %s from child with id %s", str(signal), child.getId())
        else:
            pass
    
    # *** custom recurrent tasks ***

    async def tcpServer__(self):
        try:
            self.server = await asyncio.start_server(self.handler__, "", self.port)
        
        except asyncio.CancelledError:
            self.logger.info("tcpServer__ %i: cancel")
            self.server = None
        
        except Exception as e:
            self.logger.warning("tcpServer__: failed with '%s'", str(e))
            self.logger.warning("tcpServer__: will try again in %s secs", self.pause)
            await asyncio.sleep(self.pause)
            self.tasks.tcp_server = await reSchedule(self.tcpServer__)
            
        else:
            self.logger.debug("tcpServer__ : new server waiting")


    # *** internal ***

    @verbose
    async def handler__(self, reader, writer):
        self.logger.debug("handler__ : new connection for %s", self.getInfo())
        
        if len(self.children)>self.max_clients:
            self.logger.warning("handler__ : max number of connections is %s", self.max_clients)
            return
        
        child_connection = TCPConnectionThread(reader = reader, writer = writer, parent = self)
        await child_connection.run()
        await self.addChild(child_connection)


if __name__ == "__main__":
    # loglev = logging.DEBUG
    loglev = logging.INFO

    logger = logging.getLogger("MasterTCPServerThread")
    logger.setLevel(loglev)
    logger = logging.getLogger("TCPConnectionThread")
    logger.setLevel(loglev)

    thread = MasterTCPServerThread(
        parent = None,
        name = "TCPServer"
        )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(thread.run())
