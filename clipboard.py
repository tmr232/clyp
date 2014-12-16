import contextlib
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Types
NULL = 0

GMEM_MOVEABLE = 0x0002
CF_TEXT = 1


def bool_errcheck(result, func, args):
    if not result:
        raise ctypes.WinError()
    return args


def null_errcheck(result, func, args):
    if not result:
        raise ctypes.WinError()
    return args


def errcheck_expect_null(result, func, args):
    if result:
        raise ctypes.WinError()
    return args


def lasterror_errcheck(result, func, args):
    if ctypes.get_last_error():
        raise ctypes.WinError()


def wrap_function(name, library, restype, params, errcheck=None):
    prototype = ctypes.WINFUNCTYPE(restype, *(param.type for param in params))
    paramflags = tuple(param.paramflags for param in params)
    wrapper = prototype((name, library), paramflags)
    wrapper.errcheck = errcheck

    return wrapper


class Parameter(object):
    def __init__(self, name, type_, default=None, out=False):
        self._name = name
        self._type = type_
        self._out = out
        self._default = default

    @property
    def flag(self):
        if self._out:
            return 2
        else:
            return 1

    @property
    def type(self):
        return self._type

    @property
    def paramflags(self):
        paramflags = (self.flag, self._name, self._default)
        if self._default is None:
            return paramflags[:-1]
        else:
            return paramflags


OpenClipboard = wrap_function(name="OpenClipboard",
                              library=user32,
                              restype=wintypes.BOOL,
                              params=[
                                  Parameter("hWndNewOwner", wintypes.HWND, default=0)
                              ],
                              errcheck=bool_errcheck)

CloseClipboard = wrap_function(name="CloseClipboard",
                               library=user32,
                               restype=wintypes.BOOL,
                               params=[],
                               errcheck=bool_errcheck)

EmptyClipboard = wrap_function(name="EmptyClipboard",
                               library=user32,
                               restype=wintypes.BOOL,
                               params=[],
                               errcheck=bool_errcheck)

SetClipboardData = wrap_function(name="SetClipboardData",
                                 library=user32,
                                 restype=wintypes.BOOL,
                                 params=[
                                     Parameter("uFormat", wintypes.UINT),
                                     Parameter("hMem", wintypes.HANDLE)
                                 ],
                                 errcheck=null_errcheck)

GetClipboardData = wrap_function(name="GetClipboardData",
                                 library=user32,
                                 restype=wintypes.HGLOBAL,
                                 params=[
                                     Parameter("uFormat", wintypes.UINT, default=CF_TEXT)
                                 ],
                                 errcheck=null_errcheck)


def globallock_errcheck(result, func, args):
    if not result:
        raise ctypes.WinError()
    return ctypes.c_char_p(result)


GlobalLock = wrap_function(name="GlobalLock",
                           library=kernel32,
                           restype=wintypes.LPVOID,
                           params=[
                               Parameter("hMem", wintypes.HGLOBAL)
                           ],
                           errcheck=globallock_errcheck)

GlobalUnlock = wrap_function(name="GlobalUnlock",
                             library=kernel32,
                             restype=wintypes.BOOL,
                             params=[
                                 Parameter("hMem", wintypes.HGLOBAL)
                             ],
                             errcheck=lasterror_errcheck)

GlobalAlloc = wrap_function(name="GlobalAlloc",
                            library=kernel32,
                            restype=wintypes.HGLOBAL,
                            params=[
                                Parameter("uFlags", wintypes.UINT, default=GMEM_MOVEABLE),
                                Parameter("dwBytes", wintypes.UINT)
                            ],
                            errcheck=null_errcheck)

GlobalFree = wrap_function(name="GlobalFree",
                           library=kernel32,
                           restype=wintypes.HGLOBAL,
                           params=[
                               Parameter("hMem", wintypes.HGLOBAL)
                           ],
                           errcheck=errcheck_expect_null)


@contextlib.contextmanager
def clipboard(hWndNewOwner=NULL):
    try:
        OpenClipboard(hWndNewOwner)
        yield
    finally:
        CloseClipboard()


@contextlib.contextmanager
def get_global_memory(handle):
    memory = GlobalLock(handle)

    yield memory

    GlobalUnlock(handle)


@contextlib.contextmanager
def global_alloc(flags, size):
    handle = GlobalAlloc(flags, size)

    yield handle

    GlobalFree(handle)


@contextlib.contextmanager
def global_copy(data):
    c_data = ctypes.create_string_buffer(data)
    with global_alloc(GMEM_MOVEABLE, ctypes.sizeof(c_data)) as handle:
        with get_global_memory(handle) as memory:
            ctypes.memmove(memory, c_data, ctypes.sizeof(c_data))

        yield handle


def copy(text):
    with clipboard():
        EmptyClipboard()
        # Assuming we are handling ascii
        with global_copy(text) as handle:
            SetClipboardData(CF_TEXT, handle)


def paste():
    with clipboard():
        handle = GetClipboardData(CF_TEXT)
        with get_global_memory(handle) as memory:
            return memory.value


if __name__ == '__main__':
    print paste()
    copy(paste() + b"what is this?")
    print paste()