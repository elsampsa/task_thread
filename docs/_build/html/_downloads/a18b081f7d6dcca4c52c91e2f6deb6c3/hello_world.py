"""<rtf>
The same "hello world" example we already discussed :ref:`here <threadtask>`.
<rtf>"""
import asyncio, logging, traceback
from task_thread import TaskThread, reCreate, reSchedule,\
    delete, verbose, signals
"""<rtf>
Define TaskThread by subclassing
<rtf>"""
class MyThread(TaskThread):
    """<rtf>
    Let's define a rescheduling task that sleeps for a one seconds & then reschedules itself
    <rtf>"""    
    async def helloTask__(self):
        try:
            await asyncio.sleep(1)
            self.logger.info("Hello from helloTask__ at %s", self.getId())
            self.tasks.hello_task = await reSchedule(self.helloTask__)
            return
            
        except asyncio.CancelledError:
            self.logger.critical("helloTask__: cancelling")
            
        except Exception as e:
            self.logger.info("helloTask__: failed with '%s', traceback will follow", e)
            traceback.print_exc()
            
    """<rtf>
    Remember to call the superclass constructor
    <rtf>"""    
    def __init__(self, my_id = 0, parent = None):
        super().__init__(parent = parent)
        self.my_id = my_id
            
    """<rtf>
    Create the tasks under the self.tasks namespace & initialize them to ``None``
    <rtf>"""
    def initVars__(self):
        # tasks
        self.tasks.hello = None  # self.helloTask__

    """<rtf>
    The ``helloTask__`` is started for the first time when the thread is started:
    <rtf>"""
    @verbose
    async def enter__(self):
        self.logger.info("enter__ :")
        self.tasks.hello = await reCreate(self.tasks.hello, self.helloTask__) 
        
    """<rtf>
    Define what happens at thread exit: delete any running tasks
    <rtf>"""
    @verbose
    async def exit__(self):
        """Close sockets, databases, etc.  Overwrite in child class.
        """
        self.tasks.hello = await delete(self.tasks.hello)
        self.logger.info("exit__ : finished")


    """<rtf>
    Here we would define how signals from a parent are handled.  In this example case nothing.
    <rtf>"""
    @verbose
    async def signalHandler__(self, signal):
        self.logger.info("signalHandler__ : got signal %s", signal)

    def getId(self):
        return self.my_id

    def getInfo(self):
        return "<MyThread "+str(self.my_id)+">"
    
    
"""<rtf>
Let's run MyThread!  Terminate by pressing CTRL-C.
<rtf>"""
if __name__ == "__main__":
    loglev = logging.DEBUG

    logger = logging.getLogger("MyThread")
    logger.setLevel(loglev)

    thread = MyThread(my_id = "main_thread", parent = None) # no parent, this is the main thread
    loop = asyncio.get_event_loop()
    loop.run_until_complete(thread.run())

