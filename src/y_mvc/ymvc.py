'''
Created on 24 Mar 2013

@author: Dave Wilson
'''

from y_signal.ysignal import Ysignal
from functools import wraps
import inspect

_SIGNAL = 'uniqueSignalKeyName'
_SIGNAL_ATTR = 'Attr'
_SIGNAL_MSG = 'Msg'
_SIGNAL_KW = 'Kw'
_SIGNAL_MSGKW = 'MsgKw'


def messageSignal(message):
    '''Returns a tuple representing a message signal'''
    return (_SIGNAL_MSG, message)


def keywordsSignal():
    '''Returns a tuple representing a keyword signal'''
    return (_SIGNAL_KW,)


def messsageWithKeywordsSignal(message):
    '''Returns a tuple representing a message keyword signal'''
    return (_SIGNAL_MSGKW, message)


def attributeSignal():
    '''Returns a tuple representing a attribute signal'''
    return (_SIGNAL_ATTR,)


def onMsgSignal(message):
    '''Decorates a method to only be called if the message matches the signal
    or if not called with a signal'''
    def decorator(target):
        target._signal = messageSignal(message)

        @wraps(target)
        def wrapper(self, *args, **kwargs):
            signal_call = kwargs.pop(_SIGNAL, None)
            signalMatches = signal_call == target._signal
            if not signal_call or signalMatches:
                return target(self, *args, **kwargs)
        return wrapper
    return decorator


def onKwSignal(target):
    '''Decorates a method to only be called if the keywords match
    or if not called with a signal'''
    target._signal = keywordsSignal()
    targetArgs = inspect.getargspec(target).args
    targetArgs.remove('self')
    targetArgs = set(targetArgs)

    @wraps(target)
    def wrapper(self, *args, **kwargs):
        signal_call = kwargs.pop(_SIGNAL, None)
        signalMatches = signal_call == target._signal
        keywordsMatch = set(kwargs.keys()) == targetArgs
        if not signal_call or (signalMatches and keywordsMatch):
            return target(self, *args, **kwargs)
    return wrapper


def onAttrSignal(target):
    '''Decorates a method to only be called if the keyword matches the
    attribute of the model that changed or if not called with a signal'''
    target._signal = attributeSignal()
    targetArgs = inspect.getargspec(target).args
    targetArgs.remove('self')
    target._attributes = targetArgs

    @wraps(target)
    def wrapper(self, *args, **kwargs):
        signal_call = kwargs.pop(_SIGNAL, None)
        if not signal_call or (signal_call == target._signal and
                               kwargs.keys() == target._attributes):
            return target(self, *args, **kwargs)
    return wrapper


class YmvcBase(object):
    '''YmvcBase object for signal communication in ymvc'''
    def __init__(self, useThread=True):
        '''Initialise attributes'''
        self._ySignal = Ysignal(useThread)

    def bind(self, slot):
        '''bind a slot'''
        self._ySignal.bind(slot)

    def unbind(self, slot):
        '''Remove slot from the list of listeners'''
        self._ySignal.unbind(slot)

    def unbindAll(self):
        '''Remove all slots'''
        self._ySignal.unbindAll()

    def waitInQueue(self):
        '''wait in the signal queue till current signals are done'''
        self._ySignal.waitInQueue()

    def waitTillQueueEmpty(self):
        '''Wait till the queue is empty (not reliable!)'''
        self._ySignal.waitTillQueueEmpty()

    def notifyMsg(self, message):
        '''Calls methods decorated with onMessageSignal'''
        kwargs = {_SIGNAL: messageSignal(message)}
        return self._ySignal.emit(**kwargs)

    def notifyKw(self, **kwargs):
        '''Sends a keywords notification to all slots interested
        Decorate slots with onNotifyKw(*keywords)'''
        kwargs[_SIGNAL] = keywordsSignal()
        return self._ySignal.emit(**kwargs)


class View(YmvcBase):
    '''Communicates from your view to the controller'''
    def __init__(self, gui):
        super(View, self).__init__(False)
        self.gui = gui
        self.controller = None

    def setController(self, controller, *args, **kwargs):
        '''Set the controller related to this view'''
        self.controller = controller(self.gui, *args, **kwargs)


class Model(YmvcBase):
    '''Contains the data of your application'''

    _signaledAttr = []

    def __init__(self, *attributes):
        '''Set the attributes you want to observe changes
        Decorate slots with onAttr(attribute)'''
        super(Model, self).__init__()
        self._signaledAttr = attributes

    def bind(self, slot, immediateCallback=True):
        '''binds a slot if it is an attribute slot emits its value'''
        super(Model, self).bind(slot)
        if immediateCallback and slot._signal == attributeSignal():
            self.slotGetAttr(slot)

    def __setattr__(self, name, value):
        '''Add a _setattrCall to the queue if listed in _signaledAttr'''
        if not hasattr(self, name):
            return YmvcBase.__setattr__(self, name, value)

        if name in self._signaledAttr:
            if self._ySignal.useThread:
                future = self._ySignal.threadPoolExe.submit(
                                                self._setattrCall, name, value)
                future.add_done_callback(self._ySignal.slotCheck)
                return future
            else:
                self._setattrCall(name, value)
        else:
            return YmvcBase.__setattr__(self, name, value)

    def _setattrCall(self, name, value):
        '''Sets an attributes value and then sends a signal of its new value'''
        YmvcBase.__setattr__(self, name, value)
        kwargs = {_SIGNAL: attributeSignal(), name: getattr(self, name)}
        self._ySignal._emitCall(**kwargs)

    def slotGetAttr(self, slot):
        '''Emit the attribute for this slot only'''
        name = slot._attributes[0]
        kwargs = {_SIGNAL: attributeSignal(), name: getattr(self, name)}
        return self._ySignal.emitSlot(slot, **kwargs)


class Controller(object):
    '''Communicates between a view and models'''
    def __init__(self, gui, *args, **kwargs):
        '''Sets up the view/controller pairing'''
        self.gui = gui
