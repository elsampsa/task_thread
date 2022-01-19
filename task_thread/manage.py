"""manage.py : recurrent task creation, rescheduling and cancelling

* Copyright: 2022 Sampsa Riikonen
* Authors  : Sampsa Riikonen
* Date     : 1/2022
* Version  : 0.1

This file is part of the task_thread library

Licensed according to the MIT License.  Please see file COPYING.MIT for more details.
"""
import asyncio

async def reCreate(task_ref, cofunc, *args, **kwargs):
    """Task book-keeping and management: create a task
    
    :param task_ref:  a reference to the task.  Can be None (implicating this is a new task)
    :param cofunc:    cofunction representing the tasks functionality
    :param *args:     passed on to the confunction
    :param **kwargs:  passed on to the confunction
    
    ::
    
        # in your class' constructor:
        self.your_task = None

        # later on, in your async code:
        self.your_task = await reCreate(self.your_task, self.yourTask__, some_parameter)
    
    - If reference is not None, cancels the task
    - Creates a new task and returns it
    """
    if task_ref is not None:
        if not asyncio.isfuture(task_ref):
            print("reCreate: WARNING:", task_ref, "is not a task")
            return None
        task_ref.cancel()
        try:
            await asyncio.wait_for(task_ref, timeout = 15)
        except Exception as e:
            print("WARNING: reCreate failed with", e, "for task", str(task_ref))
    task = asyncio.get_event_loop().create_task(cofunc(*args, **kwargs))
    return task
   
   
async def reSchedule(cofunc, *args, **kwargs):
    """Task book-keeping and management: re-schedule a task
    
    ::
    
        # inside the co-function that represent a task:
        self.your_task = await reSchedule(self.your_task, some_parameter, task_id = task_id); return
    
    """
    task = asyncio.get_event_loop().create_task(cofunc(*args, **kwargs))
    return task
    
   
async def delete(task_ref):
    """Task book-keeping and management: delete a task
    
    ::
    
        self.your_task = await delete(self.your_task)
    
    """
    if task_ref is not None:
        if task_ref.done():
            pass
        else:
            task_ref.cancel()
            try:
                await asyncio.wait_for(task_ref, timeout = 10)
            except Exception as e:
                print("WARNING: delete failed with", e, "for task", str(task_ref))
    return None

