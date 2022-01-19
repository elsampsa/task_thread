import asyncio, logging
import traceback

from task_thread import TaskThread, reCreate, reSchedule,\
    delete, MessageSignal, verbose, signals


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
        self.tasks.read_socket = await reCreate(self.tasks.read_socket, self.readSocket__)


    @verbose
    async def exit__(self):
        self.tasks.read_socket = await delete(self.tasks.read_socket)
        self.tasks.write_socket = await delete(self.tasks.write_socket)
        self.logger.debug("exit__: bye!")


    async def readSocket__(self):
        try:
            try:
                packet = await self.reader.read()
            except Exception as e:
                self.logger.warning("readSocket__ : reading failed : '%s'", e)
                self.logger.info("readSocket__: tcp connection %s terminated", self.getInfo())
                await self.terminate()
            else:
                if len(packet) > 0:
                    # all good!  keep on reading = reschedule this
                    self.logger.info("readSocket__: got packet %s", packet)
                    self.tasks.read_socket = await reSchedule(self.readSocket__); return
                else:
                    self.logger.info("readSocket__: client at %s closed connection", self.peername)
                    await self.terminate()

        except asyncio.CancelledError:
            self.logger.info("readSocket__ : cancelling %s", self.getInfo())
            
        except Exception as e:
            self.logger.warning("readSocket__: failed with '%s'", e)
            await self.terminate()
        
        
    async def writeSocket__(self, packet):        
        try:
            self.writer.write(packet)
            # await self.writer.drain() # this would flush
        except Exception as e:
            self.logger.warning("writeSocket__ : writing failed : '%s'", e)
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
        if isinstance(signal, MessageSignal):
            self.logger.info("Got message %s from child with id %s", signal.getMessage(), child.getId())
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
    loglev = logging.DEBUG

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
