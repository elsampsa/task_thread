.. _intro:

.. A link to :ref:`intro <intro>`

About TaskThread
================

*Never use asyncio.wait again*

TaskThread is a collection of tools, conventions and a base class that organizes 
your asyncio python programs seamlessly into hierarchical, well-organized structures.

These structures are analogical to threads and have a thread-like API.

Let's illustrate what all this is about by an example.

A Sample Problem
----------------

Let's consider a rather complex application which:

- Exposes a TCP server
- The server accepts various client connections from LAN
- Server processes the incoming data and reconstructs data frames from packets received from individual TCP client connections
- Processed data from each TCP client is forwarded through websockets to a final destination (say, to cloud)
- The processed data is also written into a database

We can see there is a lot of i/o waiting and "multiplexing" going on that can get messy.

When using TaskThread, you start unravelling a problem by identifying hierarchies.

In the present case, a solution, described as a hierarchical list, could look like this:

::

    MasterThread
        TCPServerThread
            TCPConnectionThread
                DataProcessorThread
            TCPConnectionThread
                DataProcessorThread
            ...
        WebsocketMasterThread
            WebSocketSubThread
            WebSocketSubThread
            ...
        DatabaseThread


(another kind of hierarchy to solve the problem is, of course, also possible)

``MasterThread`` starts the ``TCPServerThread`` which then starts ``TCPConnectionThread`` s on demand.

Each ``TCPConnectionThread`` starts a ``DataProcessorThread`` which reconstructs the packets from indicidual ``TCPConnectionThread`` s.

All data flows to upwards in the tree into ``MasterThread`` which then passes it onto to ``WebsocketMasterThread`` and from there to individual
``WebSocketSubThread`` s. ``MasterThread`` passes the data also to ``DatabaseThread``.

Let's add this data flow to the hierarchical list:

::

    MasterThread
        TCPServerThread: UP: data
            TCPConnectionThread: UP: data
                DataProcessorThread: IN: packets, UP: data
            TCPConnectionThread
                DataProcessorThread
            ...
        WebsocketMasterThread: IN: data
            WebSocketSubThread: IN data
            WebSocketSubThread
            ...
        DatabaseThread: IN: data

Here ``UP`` designates data going upwards in the tree, while ``IN`` shows incoming data at deeper level threads.

Notice that there is not any intercommunication within this tree that is not strictly between a parent and a child.

Threads, how?
-------------

So, how to implement such "threads" ?  After all this is asyncio, not multithreading!

Well, the entities named here ``MasterThread``, ``TCPServerThread``, etc. are not really "threads", but collection of asyncio **tasks** grouped together in a smart way - thus the name TaskThread.  
The intercom between the "threads" is done using asyncio **queues**.

Let's take a deeper look on the **tasks** and **queues**:

``DataProcessorThread`` receives packets (via a listening **task**) through a queue from ``TCPConnectionThread``.  After reconstructing
some data from the packets using a **task**, ``DataProcessorThread`` has a **task** that sends the dataframes to ``TCPConnectionThread`` through another asyncio **queue** which 
``TCPConnectionThread`` is listening with a **task**, etc.

These **queues** and listener **tasks** work seamlessly and are hidden from the TaskThread API user.

At the core of TaskThread philosophy lies **rescheduling tasks**, i.e. asyncio tasks that reschedule themselves, giving the appearance of "threads" and a thread-like API.

The only thing the API user needs to worry about, is how to initiate, re-schedule and terminate these tasks within their TaskThread implementation.

Advantages
----------

Have you ever run into a situation where you have a complex asyncio program running tons of simultaneous tasks?   

For example, you need to run ``asyncio.wait`` to "poll" several tasks to see if the tasks have finished or not and then your program's logic is altered based on that result,
creating an asynchronous mess, maybe even runaway tasks.

Well, you don't need to touch ``asyncio.wait`` ever again, after starting to use TaskThread.  

Your programs will also become naturally well-organized into threads that have
separation of concerns and restricted communication - in accordance with the `HIMO principle <https://medium.com/@sampsa.riikonen/a-roadtrip-between-object-oriented-and-functional-programming-d5161dc19052>`_.

I hope you got all warmed up by now.  Exciting, right!?

Next we will take a look at :ref:`an anatomy of a TaskThread <thread>`.


