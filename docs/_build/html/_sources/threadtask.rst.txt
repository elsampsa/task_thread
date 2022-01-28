
.. _threadtask:

Threads and Tasks
=================

So, now you have been initiated on how to create a TaskThread and rescheduling tasks and signals.

Let's bring it all together.

::

    import asyncio, logging, traceback
    from task_thread import TaskThread, reCreate, reSchedule,\
        delete, verbose, signals

Subclass the necessary methods to specify a TaskThread:

::

    class MyThread(TaskThread):

        def __init__(self, my_id = 0, parent = None):
            super().__init__(parent = parent)
            self.my_id = my_id

List your tasks:

::

        def initVars__(self):
            self.tasks.hello = None  # implementation in "self.helloTask__"

``enter__`` starts the task for the first time:

::

        @verbose
        async def enter__(self):
            self.logger.info("enter__")
            self.tasks.hello = await reCreate(self.tasks.hello, self.helloTask__) 

In ``exit__``, kill the re-scheduling tasks:

::

        @verbose
        async def exit__(self):
            self.tasks.hello = await delete(self.tasks.hello)
            self.logger.info("exit__ : finished")

For the moment, no signal handling:

::

        @verbose
        async def signalHandler__(self, signal):
            self.logger.info("signalHandler__ : got signal %s", signal)

Rest of the methods:      
        
::

        def getId(self):
            return self.my_id

        def getInfo(self):
            return "<MyThread "+str(self.my_id)+">"


Finally, define the (only) task that is running in this TaskThread:
        
::

        async def helloTask__(self):
            """A task that prints hello & re-schedules itself
            """
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

Finaly, the program runs like this:

::

    loglev = logging.DEBUG

    logger = logging.getLogger("MyThread")
    logger.setLevel(loglev)

    thread = MyThread(my_id = "main_thread", parent = None)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(thread.run())

What next?

To create a real program that does anything worthwhile, you still need to study
and understand the :ref:`examples <examples>`.
