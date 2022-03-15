.. _task:

Anatomy of a Task
=================

How do these "rescheduling tasks" that constitute a "TaskThread" look like?

Let's consider a silly task that sleeps for 1 sec and then re-schedules itself

First the imports:

::

    import asyncio, logging, traceback
    from task_thread import TaskThread, reCreate, reSchedule,\
        delete, verbose, signals

The rescheduling task itself:

::

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

with emphasis on this structure:

::

        try:
            ...
            
        except asyncio.CancelledError:
            ...
            
        except Exception as e:
            ...


i.e., if everything is ok - the task has done it's thing, say, reading payload from i/o,
writing i/o, or whatever - it then **reschedules itself**.

Rescheduling is done using the ``reSchedule`` convenience function:

::

    self.tasks.hello_task = await reSchedule(self.helloTask__)

A large group of these auto-rescheduling tasks that toil around and do their stuff, behave effectively like a "classical" running thread.

A small warning about task re-scheduling is necessary:

A function can re-schedule itself with quite a high frequency.  However, for each re-scheduling task, you should be at least, aware of the frequency: 
if a task re-schedules itself, say, a million times per second, you have created yourself a problem.

Try to keep your task's re-scheduling frequency in 100 times per second or less.  High re-scheduling frequency and its mitigation might become an issue in streaming applications,
while in most other cases you really don't need to think about it.

Finally, remember to use the correct convenience function for each case:

- When creating the task for the first time, use ``reCreate``
- When rescheduling the task, use ``reSchedule``
- When removing the task, use ``delete``

Next, let's :ref:`bring TaskThreads and tasks together <threadtask>`.

