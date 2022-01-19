"""signals.py : base definition of signals/message sent between TaskThreads

* Copyright: 2022 Sampsa Riikonen
* Authors  : Sampsa Riikonen
* Date     : 1/2022
* Version  : 0.1

This file is part of the task_thread library

Licensed according to the MIT License.  Please see file COPYING.MIT for more details.
"""

class Signal:
    """Signal base class
    """

    def __init__(self):
        pass

# Common signals to all threads
    
class TerminateSignal(Signal):
    """Parent requests the termination of the child thread
    """
    def __str__(self):
        return "<TerminateSignal>"


class CloseSignal(Signal):
    """Child informs parent that it has been closed.  Parent can stop listening to child
    """
    def __str__(self):
        return "<CloseSignal>"

# An example custom signal

class MessageSignal(Signal):
    """A generic message message signal, carrying a python object
    """
    def __init__(self, origin, message):
        self.origin = origin
        self.message = message
        
    def __str__(self):
        return "<MessageSignal from %s>" % (str(self.origin))

    def getMessage(self):
        return self.message



