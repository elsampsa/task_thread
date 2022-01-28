import asyncio, logging, traceback
from task_thread import TaskThread, reCreate, reSchedule,\
    delete, verbose, signals

"""<rtf>
Let's define a signal for parent/child communication
<rtf>"""
class MessageSignal(signals.Signal):
    def __init__(self, origin, message):
        self.origin = origin
        self.message = message
        
    def __str__(self):
        return "<MessageSignal from %s>" % (str(self.origin.getId()))

    def getMessage(self):
        return self.message

"""<rtf>
We use the same ``MyThread`` as in the previous example. 
We will use it as a basis for further subclassing
<rtf>"""
class MyThread(TaskThread):
    # as in previous example
    # ...
    #HIDE>
    async def helloTask__(self):
        try:
            await asyncio.sleep(1)
            self.logger.info("Hello from helloTask__ at %s", self.getId())
            self.tasks.hello_task = await reSchedule(self.helloTask__); return
            
        except asyncio.CancelledError:
            self.logger.critical("helloTask__: cancelling")
            
        except Exception as e:
            self.logger.info("helloTask__: failed with '%s', traceback will follow", e)
            traceback.print_exc()
            

    def __init__(self, my_id = 0, parent = None):
        super().__init__(parent = parent)
        self.my_id = my_id
        
    
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
        self.logger.info("entry point")
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
    
#<HIDE

"""<rtf>
Let's create a child thread.  This thread sends a message to it's parent every 5 seconds:
<rtf>"""
class ChildThread(MyThread):
    """<rtf>
    Define a rescheduling task that sends a message to it's parent every 5 seconds
    <rtf>"""
    async def messageTask__(self):
        try:
            await asyncio.sleep(5)
            self.logger.info("messageTask__: sending a message to parent")
            
            await self.sigFromChildToParent__(
                MessageSignal(origin = self, 
                message = "hello from child " + str(self.getId())))
            self.tasks.message_task = await reSchedule(self.messageTask__); return
            
        except asyncio.CancelledError:
            self.logger.critical("messageTask__: cancelling")
            
        except Exception as e:
            self.logger.info("messageTask__: failed with '%s', traceback will follow", e)
            traceback.print_exc()

    """<rtf>
    Add the new task to ``self.tasks`` namespace
    <rtf>"""
    def initVars__(self):
        # tasks
        self.tasks.hello   = None  # self.helloTask__
        self.tasks.message = None  # self.messageTask__
        # locks
        self.locks.message_lock = asyncio.Lock()

    """<rtf>
    Start both tasks at thread start
    <rtf>"""
    @verbose
    async def enter__(self):
        self.logger.info("enter__")
        self.tasks.hello = await reCreate(self.tasks.hello, self.helloTask__) 
        self.tasks.message = await reCreate(self.tasks.message, self.messageTask__)

    """<rtf>
    Kill both tasks at thread exit
    <rtf>"""
    @verbose
    async def exit__(self):
        self.tasks.hello = await delete(self.tasks.hello)
        self.tasks.message = await delete(self.tasks.message)
        self.logger.info("exit__ : finished")


"""<rtf>
Now the parent thread that receives signals from the child:
<rtf>"""
class ParentThread(MyThread):
    """<rtf>
    Start ``self.helloTask__`` just like in the child thread.

    The new bit here is, that we create and start a child thread at parent thread start.

    After starting, the child thread is added to the parent's registry using ``addChild``.

    You can experiment by adding more and more child threads.
    <rtf>"""
    @verbose
    async def enter__(self):
        self.logger.info("enter__")
        self.tasks.hello = await reCreate(self.tasks.hello, self.helloTask__) 
        child_thread = ChildThread(my_id = "subthread", parent = self)
        await child_thread.run()
        await self.addChild(child_thread)
    
    """<rtf>
    Define how we handle those signals coming from the running child thread:
    <rtf>"""
    @verbose
    async def childsignalHandler__(self, signal, child):
        self.logger.debug("childsignalHandler__ : got signal %s from child %s", signal, child.getId())
        if isinstance(signal, MessageSignal):
            self.logger.info("Got message %s from child with id %s", 
            signal.getMessage(), child.getId())
        else:
            pass

"""<rtf>
Please note that you can also start child threads "dynamically", i.e. anywhere in your classes internal methods/recheduling tasks, not just at ``enter__``.

That's it!  Nothing else is needed: when the parent thread terminates, it automagically terminates all of it's child threads.

Run the program with:
<rtf>"""
if __name__ == "__main__":
    loglev = logging.DEBUG

    logger = logging.getLogger("ParentThread")
    logger.setLevel(loglev)

    logger = logging.getLogger("ChildThread")
    logger.setLevel(loglev)
    
    thread = ParentThread(my_id = "parent_thread", parent = None) # no parent, this is the main thread
    loop = asyncio.get_event_loop()
    loop.run_until_complete(thread.run())
"""<rtf>
Terminate by pressing CTRL-C.
<rtf>"""
