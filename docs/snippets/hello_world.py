import asyncio, logging
import traceback

from task_thread import TaskThread, reCreate, reSchedule,\
    delete, verbose, signals


class MessageSignal(signals.Signal):
    """A generic message message signal, carrying a python object
    """
    def __init__(self, origin, message):
        self.origin = origin
        self.message = message
        
    def __str__(self):
        return "<MessageSignal from %s>" % (str(self.origin.getId()))

    def getMessage(self):
        return self.message


"""<rtf>

Some rtf comments here

<rtf>"""


class MyThread(TaskThread):
    
    # *** recurrent tasks that define the functionality of this thread ***
    
    async def helloTask__(self):
        """A task that prints hello & re-schedules itself
        """
        try:
            # *** define your recurrent task's functionality here ***
            await asyncio.sleep(1)
            self.logger.info("Hello from helloTask__ at %s", self.getId())
            self.tasks.hello_task = await reSchedule(self.helloTask__); return
            
        except asyncio.CancelledError:
            self.logger.critical("helloTask__: cancelling")
            
        except Exception as e:
            self.logger.info("helloTask__: failed with '%s', traceback will follow", e)
            traceback.print_exc()
            
    # *** class ctor ***

    def __init__(self, my_id = 0, parent = None):
        super().__init__(parent = parent)
        self.my_id = my_id
        
    
    # *** reimplemented virtual methods: ***
    
    def initVars__(self):
        """Create & initialize here your tasks with none & create your locks
        """
        # tasks
        self.tasks.hello = None  # self.helloTask__
        
    
    @verbose
    async def enter__(self):
        """Everything starts from here.  This cofunction is awaited (i.e. not scheduled as a task)
        
        - Await for something critical
        - Shedule the re-scheduling tasks
        """
        self.logger.info("enter__ :")
        self.tasks.hello = await reCreate(self.tasks.hello, self.helloTask__) 
        
    
    @verbose
    async def exit__(self):
        """Close sockets, databases, etc.  Overwrite in child class.
        """
        self.tasks.hello = await delete(self.tasks.hello)
        self.logger.info("exit__ : finished")


    @verbose
    async def signalHandler__(self, signal):
        """Handles a signal that was sent to this thread using insertSignal
        
        - Return True if thread should keep on running
        - Return False if thread should exit (say, in the case of some fatal error)
        
        Do subclass this.
        """
        self.logger.info("signalHandler__ : got signal %s", signal)
    
    
    def getId(self):
        """Do subclass this.
        
        Return a unique id for this VirtualThread.
        """
        return self.my_id
        

    def getInfo(self):
        """Do subclass this
        
        Returns information string about this thread
        """
        return "<MyThread "+str(self.my_id)+">"
    
    

if __name__ == "__main__":
    loglev = logging.DEBUG

    logger = logging.getLogger("MyThread")
    logger.setLevel(loglev)

    thread = MyThread(my_id = "main_thread", parent = None) # no parent, this is the main thread
    loop = asyncio.get_event_loop()
    loop.run_until_complete(thread.run())
    
