"""task_thread.py : TaskThread base class definition

* Copyright: 2022 Sampsa Riikonen
* Authors  : Sampsa Riikonen
* Date     : 1/2022
* Version  : 0.1

This file is part of the task_thread library

Licensed according to the MIT License.  Please see file COPYING.MIT for more details.
"""

# stdlib
import logging
import traceback
import asyncio
import signal as posix_signal
import functools

from task_thread.decorator import verbose
from task_thread.base import signals
from task_thread.manage import reCreate, reSchedule, delete

LOWLEVEL = logging.DEBUG-1

class Namespace:
    
    def __init__(self):
        pass


class TaskThread:
    
    max_qsize = 100

    def __init__(self, parent = None):
        """If you need to subclass your own init, remember to call in your subclassed init this with:
        
        ::
        
            super().__init__(parent = parent)
        
        """
        self.parent = parent
        maxsize = self.max_qsize
        # each thread has a queue where it receives signals.  
        # This queue receives signals and payload from the Parent:
        self.input_queue = asyncio.Queue(maxsize = maxsize) 
        
        # this is used by the children thread.  Parent listens to this queue.
        self.output_queue = asyncio.Queue(maxsize = maxsize) 
        
        self.children = []
        
        loop = asyncio.get_event_loop()
        
        self.main_loop = None
        self.child_listener_tasks = {} # key: child TaskThread, value: the task that is listening to that children TaskThread
        
        self.tasks = Namespace() # organize your (recurrent) tasks here
        self.locks = Namespace() # organize your locks here
        
        self.locks.children = asyncio.Lock() # lock to protect manipulations on child threads
        
        # If this is the "master" thread, add handler for SIGINT & SIGTERM : https://pymotw.com/3/asyncio/unix_signals.html
        if self.parent is None:
            loop.add_signal_handler(
                posix_signal.SIGINT,
                functools.partial(self.sig_handler__),
                )
            loop.add_signal_handler(
                posix_signal.SIGTERM,
                functools.partial(self.sig_handler__),
                )

        self.exit_event = asyncio.Event()
        self.exit_event.clear()

        self.running = False

        self.setLogging()  
        self.initVars__()


    def setLogging(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        if not self.logger.hasHandlers():
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)    
            self.logger.addHandler(ch)

        
    def sig_handler__(self):
        """Attach SIGINT handler for master threads.  Don't subclass.
        """
        self.logger.error("SIGINT or SIGTERM")
        asyncio.get_event_loop().create_task(self.insertSignal(signals.TerminateSignal()))
        

    async def join(self):
        await self.exit_event.wait()


    async def insertSignal(self, signal):
        """Puts a signal to this thread.
        
        Typically from parent to child (this) thread.  The signal goes to self.input_queue.
        
        A signal should be a subclass of task_thread.base.signal.Signal.
        
        With signals you can command child threads to do specific tasks.  Shutdown, reconnect, etc.
        
        Don't subclass.
        """
        try:

            if not self.running:
                self.logger.warning("insertSignal: signal %s to thread %s that is not running!", signal, self.getInfo())

            assert(issubclass(signal.__class__, signals.Signal))
            if self.input_queue.full():
                await self.inputOverflowHandler__(self.input_queue)
            await self.input_queue.put(signal)
        
        except Exception as e:
            self.logger.warning("insertSignal failed with %s, traceback will follow", e)
            traceback.print_exc()
            

    async def __call__(self):
        """Alias
        """
        await self.run()


    async def run(self):        
        """Runs this TaskThread.  Dont't subclass.
        
        This goes on under-the-hood:
        
        - Awaits for cofunction enter__, which is the starting point for your TaskThread's functionality
        - When running this TaskThread, always await for this cofunction (never schedule it as a task)
        - Or run this method with asyncio.run_until_complete
        """
        await self.enter__()
        
        """
        What is going on here?
        
        - Threads and their childs threads schedule and re-schedule new tasks constantly into the event loop
        - However, in order not to exit the event loop completely, we must keep on awaiting continuously
        - This continuous await is done solely by the master thread
        """
        if self.parent is None: # doesn't have a parent, so this is the master thread
            await self.mainLoop__() # await continuously for messages
            
        else: # this is a child thread: shedule the continuous waiting for messages as a task & exit
            self.main_loop = await reCreate(self.main_loop, self.mainLoop__)
            
    
    # @verbose
    async def mainLoop__(self):
        """Infinite loop.  Don't subclass.
        """
        try:
            self.running = True
            while await self.watchSignals__(): # run loop until watchSignals returns False
                pass
            self.running = False
            # if this is a child thread, it tells parent to stop listening to it:
            await self.sigFromChildToParent__(signals.CloseSignal()) 
            await self.exit__()
            async with self.locks.children: # just in case if the list is modified during awaits
                for child in self.children:
                    self.logger.log(LOWLEVEL,"mainLoop__ : sending terminate to %s", child)
                    # await child.insertSignal(signals.TerminateSignal())
                    await child.terminate()
                    await child.main_loop # wait till child's main_loop task has been finished
                    
            self.logger.log(LOWLEVEL,"bye")
            self.exit_event.set()

        except asyncio.CancelledError:
            self.logger.critical("mainLoop__: main loop cancelled!  This should not happen!")
            traceback.print_exc()
            
        except Exception as e:
            self.logger.warning("mainLoop__: terminated with %s, traceback will follow", e)
            traceback.print_exc()
            
    
    @verbose
    async def watchSignals__(self) -> bool:
        """Handles a signal that was sent to this thread using insertSignal
        
        - This method is called continuously by self.mainLoop__, until it returns False
        - Checks that signals are of correct type (subclass of signals.Signal)
        - If it's a terminate signal then return False
        - Otherwise call self.signalHandler__
        - Do not subclass this method
        """
        signal = await self.input_queue.get()
        
        assert(issubclass(signal.__class__, signals.Signal))
        if (isinstance(signal, signals.TerminateSignal)):
            return False
        
        res = await self.signalHandler__(signal)
        
        return res

        
    @verbose
    async def terminate(self):
        """Instruct this TaskThread to terminate itself
        
        - When a VirtualThread is terminated, it automatically requests the termination of all it's child threads
        - Do not subclass this method
        """
        if self.running:
            await self.insertSignal(signals.TerminateSignal())
        

    @verbose
    async def addChild(self, child):
        """Add a children
        
        - Remember that you might want to add some re-scheduling listeners per each child
        - Do not subclass this method
        """
        async with self.locks.children:
            self.logger.log(LOWLEVEL,"addChild: adding child %s to parent %s", str(child), str(self))
            self.children.append(child)
            if child not in self.child_listener_tasks:
                self.child_listener_tasks[child] = None
            self.child_listener_tasks[child] = await reCreate(
                    self.child_listener_tasks[child],
                    self.childListenerTask__, 
                    child
                )
            

    @verbose
    async def delChild(self, child):
        """Deletes / removes a children.  
        
        - Do not subclass this method
        """
        async with self.locks.children:
            if (child in self.children):
                self.logger.log(LOWLEVEL,"delChild: removing child %s from parent %s", str(child), str(self))
                self.children.remove(child)
                await child.terminate()
                self.logger.log(LOWLEVEL,"delChild: removed child %s from parent %s", str(child), str(self))
        
        
    async def childListenerTask__(self, child):
        """Adds & removes listeners for child TaskThreads.  
        - There is a task of this kind per each child
        - Do not subclass this method
        """
        try:
            async def reschedule(): # a shorthand for re-scheduling this method and keep on listening
                self.child_listener_tasks[child] = await reSchedule(self.childListenerTask__, child)
                
            self.logger.log(LOWLEVEL,"childListenerTask__: listening child %s. output_queue: %s", child.getInfo(), child.output_queue)
            # print("childListenerTask__: listening child %s", child.getInfo())

            signal = await child.output_queue.get() # output queue is for child --> parent communication
            
            if isinstance(signal, signals.CloseSignal):
                self.logger.log(LOWLEVEL,"childListenerTask__: stop listening child %s", child)
                # no re-scheduling, just exit listener
                # removing children from self.child_listener_tasks must be done here!
                try:
                    self.child_listener_tasks.pop(child)
                except KeyError:
                    self.logger.warning("childListenerTask__: could not remove child %s", child)
                return # no re-scheduling
            
            else:
                self.logger.log(LOWLEVEL,"childListenerTask__: got signal %s from child %s", signal, child.getInfo())
                await self.childsignalHandler__(signal, child)
                self.logger.log(LOWLEVEL,"childListenerTask__: rescheduling child %s", child.getInfo())
                await reschedule(); return
                
        except asyncio.CancelledError:
            self.logger.critical("childListenerTask__: cancelling, but should not get cancelled!")
            
        except Exception as e:
            self.logger.warning("childListenerTask__: '%s', traceback will follow", str(e))
            traceback.print_exc()
        
    
    def findChild(self, _id = None, _class = None):
        """Find a child thread corresponding to a unique id number, class or both.  
        
        Don't subclass.
        """
        # self.logger.log(LOWLEVEL,"findChild: id: %s, class: %s", _id, str(_class))
        for child in self.children:
            # self.logger.log(LOWLEVEL,"findChild: search: id: %s, class: %s", child.getId(), str(child.__class__))
            if (_id is not None) and (_class is not None):
                if ( child.getId()==_id and issubclass(child.__class__, _class) ):
                    return child
            elif (_id is not None) and child.getId()==_id:
                return child
            elif issubclass(child.__class__, _class):
                return child
        return None
            

    def getChildIds(self, _class = None):
        """Get all child ids corresponding to a certain class.  
        
        Don't subclass.
        """
        ids = []
        for child in self.children:
            _id = None
            if (_class is not None) and issubclass(child.__class__, _class):
                _id = child.getId()
            elif _class is None:
                _id = child.getId()
        
            if _id is not None:
                ids.append(_id)
        
        return ids
                
        
    @verbose
    async def sigFromParentToChild__(self, signal):
        """Send signal to all child threads.  
        
        Don't subclass.
        """
        async with self.children.lock:
            # self.logger.log(LOWLEVEL,"sigFromParentToChild__: parent %s", str(self))
            for child in self.children:
                # self.logger.log(LOWLEVEL,"sigFromParentToChild__: parent %s send signal %s, children %s", str(self), str(signal), str(child))
                await child.insertSignal(signal)
            
        
    @verbose
    async def sigFromChildToParent__(self, signal):
        """Send a signal to the parent thread, by writing to self.output_queue queue.
        
        - Assume parent listening to child's out queue
        
        Don't subclass.
        """
        if self.parent is not None: 
            if self.output_queue.full():
                await self.outputOverflowHandler__(self.output_queue)
            await self.output_queue.put(signal)


    # *** methods to be subclassed ***
    
    def initVars__(self):
        """Create & initialize here your tasks with none & create your locks
        """
        raise(BaseException("virtual method"))
        #self.tasks.some_task = None
        #self.locks.some_lock = asyncio.Lock()
    
    
    @verbose
    async def enter__(self):
        """Everything starts from here.  Overwrite in child class.  This cofunction is awaited (i.e. not scheduled as a task)
        
        - Await for something critical
        - Shedule the re-scheduling tasks
        
        Do subclass this.
        """
        raise(BaseException("virtual method"))
        # self.logger.info("enter__")


    @verbose
    async def exit__(self):
        """Close sockets, databases, etc.  Overwrite in child class.
        
        Do subclass this.
        """
        # raise(BaseException("virtual method"))
        pass

    
    
    @verbose
    async def signalHandler__(self, signal):
        """Handles a signal that was sent to this thread using insertSignal
        
        - Return True if thread should keep on running
        - Return False if thread should exit (say, in the case of some fatal error)
        
        Do subclass this.
        """
        # raise(BaseException("virtual method"))
        self.logger.info("signalHandler__ : got signal %s", signal)
    
    
    @verbose
    async def childsignalHandler__(self, signal, child):
        """How to handle a certain signal coming from a child thread.
        
        Do subclass.
        """
        # raise(BaseException("virtual method"))
        self.logger.info("childsignalHandler__ : got signal %s from child %s", signal, child)
    
    
    async def inputOverflowHandler__(self, queue):
        """The incoming message queue overflows.  How to handle such situation?

        :param queue: the async queue.  Do something with it (flush maybe etc.)

        Do subclass.
        """
        self.logger.critical("overflow at input (parent->child) queue")


    async def outputOverflowHandler__(self, queue):
        """The outgoing message queue that parent listens overflows.  How to handle that?

        :param queue: the async queue.  Do something with it (flush maybe etc.)

        This should very extremely rare: it means that the parent is not reading it's child queues rapidly enough

        Do subclass.
        """
        self.logger.critical("overflow at output (child->parent) queue")


    def getId(self):
        """Do subclass this.
        
        Return a unique id for this VirtualThread.
        """
        raise(BaseException("virtual method"))
        return None
    

    def getInfo(self):
        """Do subclass this
        
        Returns information string about this thread
        """
        raise(BaseException("virtual method"))
        return None
    

