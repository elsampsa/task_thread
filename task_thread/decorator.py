"""decorator.py : decorators for coroutines to make development easier

* Copyright: 2022 Sampsa Riikonen
* Authors  : Sampsa Riikonen
* Date     : 1/2022
* Version  : 0.1

This file is part of the task_thread library

Licensed according to the MIT License.  Please see file COPYING.MIT for more details.
"""
import asyncio

def verbose(f):
    """Decorator for coroutines
    
    - Returns None if there is an exception
    - If there is an exception, an additional BaseException is raised (https://bugs.python.org/issue35867)
    - NameError, AssertionError, etc. are caught, not when the task is finished, but only when the task is garbage collected
    """
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        
        except asyncio.CancelledError as e: # propagate task cancel
            raise(e)
        
        except Exception as e: # any other exception should be reported, and BaseException raised so that the program stops
            raise(BaseException) # enable this if you wan't exceptions raised.  Good for first-stage debugging # DEBUGGING

    wrapper.__name__ = f.__name__
    wrapper.__doc__  = f.__doc__
    return wrapper

