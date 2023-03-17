
.. _thread:

Anatomy of a TaskThread
=======================

Imports
-------

The necessary imports for writing your TaskThread are:

::

    import asyncio, logging, traceback
    from task_thread import TaskThread, reCreate, reSchedule,\
        delete, verbose, signals


Subclassing
-----------

You create a custom thread by subclassing from the ``TaskThread`` base class.

The methods in ``TaskThread`` that you must override are:

::

        
    def __init__(self, parent = None)
    
    def initVars__(self)
        
    async def enter__(self)
        
    async def exit__(self)

    async def signalHandler__(self, signal)

    async def childsignalHandler__(self, signal, child)
    
    def getId(self)

    def getInfo(self)
        

Let's take a closer look at each one of these methods.  

In the ``__init__`` you *must* call the superclass method (similar to ``threading`` and ``multiprocess`` modules):

::

    def __init__(self, parent = None):
        super().__init__(parent = parent)
        # whatever extra stuff
        
In ``initVars`` you define the rescheduling tasks that define the functionality of your
TaskThread:

::

    def initVars__(self):
        """Create & initialize here your tasks with none & create your locks
        """
        self.tasks.writer = None
        self.tasks.reader = None
        # etc.
        self.locks.writer = asyncio.Lock()
        # etc.

Notice how the tasks are organized under their own namespace ``self.tasks``.
All tasks are initialized as ``None``.  There is a separate convenience 
namespace ``self.locks`` for asyncio locks.

The starting point for your thread is defined in ``enter__``:

::

    @verbose
    async def enter__(self):
        self.logger.info("enter__ : %s", self.getInfo())
        self.tasks.writer = await reCreate(self.tasks.writer, self.readerMethod__)
        self.tasks.reader = await reCreate(self.tasks.reader, self.writerMethod__)

Here we use a special decorator ``@verbose`` that makes life with asyncio a bit easier - it catches
some exceptions explicitly for you.

We start the rescheduled tasks using the convenience function ``reCreate``.  The target
of the task is ``self.readerMethod__`` where the task is defined (more on this in the
section :ref:`about tasks <task>`).

Next, you still remember the hierarchical way the threads are organized and how they
communicate?  ``signalHandler__`` defines what the TaskThread should do when it gets
a message/data **from a parent**:

::

    @verbose
    async def signalHandler__(self, signal):
        self.logger.info("signalHandler__ : got signal %s from parent", signal)

The implementation of this method depends, of course, completely on your TaskThread's
functionality.

A thread must also know what to do when it gets a signal from a child.  This is defined
in ``childsignalHandler__``:

::
    
    @verbose
    async def childsignalHandler__(self, signal, child):
        self.logger.debug("childsignalHandler__ : got signal %s from child %s", signal, child.getId())

Finally, ``getId`` returns some unique string or int corresponding to this TaskThread
(nice for search/organizational purposes), while ``getInfo`` returns a string representation
of the TaskThread (i.e. like ``__str__``).

You could write:

::

    def getId(self):
        return str(id(self))

    def getInfo(self):
        return "<MyThread "+str(self.getId())+">"
        

API Methods
-----------

By using subclassing, we have defined what our TaskThread *does*.
Next we take a look at the API methods, i.e. how to *use* a TaskThread.

Let's take a quick overview of the available methods in the TaskThread class.

However, in order to know how to *really* use these methods, you need to go through the :ref:`examples <examples>`.

A TaskThread is created like this:

::

    thread = MyThread(parent = parent)


Start running it with:

::

    await thread.run()

Stop with:

::

    await thread.stop()

and wait until it has finished:

::

    await thread.join()

A child thread can terminate itself, by calling ``self.stop()``.

Stopping a child automatically deregisters / removes it from any listening parent.

You can add a child thread to a parent thread:

::
    
    await thread.addChild(child)

After that, parent starts listening any signals from the child.

Finding a child, based on it's id, as returned by it's ``getId()`` method is done with:

::
    
    await thread.findChild(_id = _id)

Sending a signal from parent to child, i.e. down/deeper in the hierarchical parent/child
structure:

::

    await thread.sigFromParentToChild__(signal, child)

If child is replaced by ``None``, the same signal is sent to all children.

Sending a signal the other way around: from children to parent, i.e. upwards in the tree:

::
    
    await thread.sigFromChildToParent__(signal)
    

Signals
-------

Signals are those things that go to and fro between parent and child threads.

A typical signal looks like this:

::

    class MessageSignal(signals.Signal):
        """A generic message message signal, carrying a python object
        """
        def __init__(self, message):
            self.message = message
            
        def __str__(self):
            return "<MessageSignal with message %s>" % (str(self.message))

        def getMessage(self):
            return self.message

        def __call__(self):
            """syntactic sugar"""
            return self.getMessage()

Signals can carry messages, byte payload, whatever.

Next, let's take a closer look at :ref:`tasks <task>`.
