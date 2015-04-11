# -*- coding: utf-8 -*-

###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import iptv_system, printDBG
###################################################
# FOREIGN import
###################################################
import threading
import traceback
###################################################

gMainFunctionsQueue = None

class AsyncCall(object):
    def __init__(self, fnc, callback=None, callbackWithThreadID=False):
        printDBG("AsyncCall.__init__ [%s]--------------------------------------------" % fnc.__name__)
        self.Callable = fnc
        self.Callback = callback
        self.CallbackWithThreadID = callbackWithThreadID

        self.mainLock = threading.Lock()
        self.finished = False
        self.Thread   = None
        self.exceptStack = ''

    def __del__(self):
        printDBG("AsyncCall.__del__  --------------------------------------------")

    def __call__(self, *args, **kwargs):
        self.Thread = threading.Thread(target = self.run, name = self.Callable.__name__, args = args, kwargs = kwargs)
        self.Thread.start()
        return self
        
    def isFinished(self):
        return self.finished
    
    def isAlive(self):
        return None != self.Thread and self.Thread.isAlive()

    def kill(self):
        bRet = False
        self.mainLock.acquire()

        self.Callback = None
        if self.finished == False:
            if self.Thread.isAlive():
                self.Thread._Thread__stop()
            bRet = True

        self.mainLock.release()

        return bRet
        
    def getExceptStack(self):
        self.mainLock.acquire()
        exceptStack = self.exceptStack
        self.mainLock.release()
        return exceptStack

    def run(self, *args, **kwargs):
        try:
            result = self.Callable(*args, **kwargs)
        except: 
            self.mainLock.acquire()
            self.exceptStack = traceback.format_exc()
            self.mainLock.release()
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>]]]]]]]]]]]]]]]]]]]]]]]] %s" % self.exceptStack)
            return
            
        self.mainLock.acquire()

        self.finished = True
        if self.Callback:
            if self.CallbackWithThreadID:
                printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> self[%r] [%r]" % (self, self.CallbackWithThreadID))
                self.Callback(self, result)
            else:
                self.Callback(result)
            
        self.Thread   = None
        self.Callable = None
        self.Callback = None
        self.CallbackWithThreadID = None

        self.mainLock.release()

class AsyncMethod(object):
    def __init__(self, fnc, callback=None, callbackWithThreadID=False):
        printDBG("AsyncMethod.__init__ --------------------------------------------")
        self.Callable = fnc
        self.Callback = callback
        self.CallbackWithThreadID = callbackWithThreadID
        
    def __del__(self):
        printDBG("AsyncMethod.__del__  --------------------------------------------")

    def __call__(self, *args, **kwargs):
        fnc      = self.Callable
        callback = self.Callback
        callbackWithThreadID = self.CallbackWithThreadID
        self.Callable = None
        self.Callback = None
        self.CallbackWithThreadID = None
        return AsyncCall(fnc, callback, callbackWithThreadID)(*args, **kwargs)
        
class Delegate(object):
    def __init__(self, proxyFunctionQueue, fnc):
        self.function = fnc
        self.proxyQueue = proxyFunctionQueue
        self.event = threading.Event()
        self.returnValues = None
        
    def __call__(self, *args, **kwargs):
        if self.proxyQueue:
            if self.proxyQueue.mainThreadName != threading.currentThread().getName():
                self.event.clear()
            
                item = CPQItemDelegate(self.function, args, kwargs, self.finished)
                self.proxyQueue.addItemQueue(item)
                
                self.event.wait()
                returnValues = self.returnValues
                self.returnValues = None
                return returnValues
            else:
                raise BaseException("Delegate cannot be used in MainThread!")

    def finished(self, *args):
        self.returnValues = args
        self.event.set()
        
    #def __del__(self):
    #    printDBG("Delegate.__del__ ---------------------------------")

class DelegateToMainThread(Delegate):
    def __init__(self, fnc):
        global gMainFunctionsQueue
        Delegate.__init__(self, gMainFunctionsQueue, fnc)
        
    #def __del__(self):
    #    printDBG("DelegateToMainThread.__del__ ---------------------------------")
        

class MainSessionWrapper(object):
    '''
    MainSessionWrapper
    can be used only from other thread then MainThread.
    '''
    WAIT_RET = "WaitForFinish"
    def __init__(self):
        self.retVal = None
        self.event = threading.Event()
        
    def open(self, *args, **kwargs):
        DelegateToMainThread(self._open)(*args, **kwargs)
        
    def _open(self, session, *args, **kwargs):
        session.open(*args, **kwargs)

    def waitForFinishOpen(self, *args, **kwargs):
        self.event.clear()
        tmpRet = DelegateToMainThread(self._waitForFinishOpen)(*args, **kwargs)
        if tmpRet and tmpRet[0] == MainSessionWrapper.WAIT_RET: 
            self.event.wait()
            return self.retVal
        else: 
            raise BaseException("DelegateToMainThread Error")

    def _waitForFinishOpen(self, session, *args, **kwargs):
        session.openWithCallback(self._callBack, *args, **kwargs)
        return MainSessionWrapper.WAIT_RET

    def _callBack(self, *args):
        self.retVal = args
        self.event.set()

class iptv_execute(object):
    '''
    Calling os.system is not recommended, it may fail due to lack of memory,
    please use iptv_execute instead, this should be used as follow:
    ret = iptv_execute()("cmd")
    ret['sts'], ret['code'], ret['data']
    
    iptv_execute must be used outside from MainThread context, please see 
    iptv_system class from iptvtools module which is dedicated to be
    used inside MainThread context
    '''
    WAIT_RET = "WaitForFinish"
    def __init__(self):
        self.retVal = None
        self.event = threading.Event()

    def __call__(self, cmd):
        printDBG("iptv_execute.__call__: Here we must not be in main thread context: [%s]" % threading.current_thread());
        self.event.clear()
        tmpRet = DelegateToMainThread(self._system)(cmd)
        if tmpRet and tmpRet[0] == iptv_execute.WAIT_RET: 
            self.event.wait()
            ret = self.retVal
            self.retVal = None
            return ret
        else: 
            return {'sts':False}

    def _system(self, session, cmd):
        printDBG("iptv_execute._system: Here we must be in main thread context: [%s]" % threading.current_thread());
        self.iptv_system = iptv_system(cmd, self._callBack)
        return iptv_execute.WAIT_RET

    def _callBack(self, code, outData):
        printDBG("iptv_execute._callBack: Here we must be in main thread context: [%s]" % threading.current_thread());
        self.iptv_system = None
        self.retVal = {'sts':True, 'code':code, 'data':outData}
        self.event.set()

    #def __del__(self):
    #    printDBG("iptv_execute.__del__ ---------------------------------")

###############################################################################
#                          Proxy function Queue
#           can be used to run call back function from MainThread
###############################################################################
class CPQItemBase:
    def __init__(self):
        pass
        
class CPQItemDelegate(CPQItemBase):
    def __init__(self, callFnc, args, kwargs, retFnc):
        CPQItemBase.__init__(self)
        self.callFnc = callFnc
        self.args    = args
        self.kwargs  = kwargs
        self.retFnc  = retFnc

class CPQItemCallBack(CPQItemBase):
    def __init__(self, clientFunName, retValue):
        CPQItemBase.__init__(self)
        self.clientFunName = clientFunName
        self.retValue = retValue
        
class CPQParamsWrapper:
    def __init__(self, params):
        self.params = params
  
class CFunctionProxyQueue:
    def __init__(self, session):
        # read/write/change display elements should be done from main thread
        self.session = session
        self.Queue = []
        self.QueueLock = threading.Lock()
        self.mainThreadName = threading.currentThread().getName()
        self.procFun = None
        
    ############################################################
    #       This method can be called only from mainThread
    #       so there is no need to synchronize it by mutex
    ############################################################
    def setProcFun(self, fun):
        currThreadName = threading.currentThread().getName()
        if self.mainThreadName != currThreadName:
            printDBG("ERROR CFunctionProxyQueue.registerFunction: thread [%s] is not main thread" % currThreadName)
            raise AssertionError
            return False
        # field self.procFun is accessed only from main thread
        self.procFun = fun
        return True 
        
    def clearQueue(self):
        printDBG('clearQueue')
        self.QueueLock.acquire()
        self.Queue = []
        self.QueueLock.release()
        
    def addItemQueue(self, item):
        self.QueueLock.acquire()
        self.Queue.append(item)
        self.QueueLock.release()

    def addToQueue(self, funName, retValue):
        printDBG("addToQueue")
        item = CPQItemCallBack(funName, retValue)
        self.addItemQueue(item)
        
    def processQueue(self):
       # Queue can be processed only from main thread
        currThreadName = threading.currentThread().getName()
        if self.mainThreadName != currThreadName:
            printDBG("ERROR CFunctionProxyQueue.processQueue: Queue can be processed only from main thread, thread [%s] is not main thread" % currThreadName)
            raise AssertionError, ("ERROR CFunctionProxyQueue.processQueue: Queue can be processed only from main thread, thread [%s] is not main thread" % currThreadName)
            return False
            
        while True:
            QueueIsEmpty = False
            
            self.QueueLock.acquire()
            if len(self.Queue) > 0:
                #get CPQItemCallBack from mainList
                item = self.Queue.pop(0)
                printDBG("CFunctionProxyQueue.processQueue")
            else:
                QueueIsEmpty = True 
            self.QueueLock.release()
            
            if QueueIsEmpty: return
                
            if isinstance(item, CPQItemCallBack) and None != self.procFun:
                self.procFun(item)
            elif isinstance(item, CPQItemDelegate) and hasattr(item.callFnc, '__call__') and hasattr(item.retFnc, '__call__') :
                item.retFnc(item.callFnc(self.session, *item.args, **item.kwargs))
            else:
                printDBG("processQueue WRONG TYPE of proxy queue item")

        # and while True:
        return
