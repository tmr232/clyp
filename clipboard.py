import contextlib
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Types
BOOL = ctypes.c_uint32
HWND = ctypes.c_uint32
NULL = 0

GMEM_MOVEABLE = 0x0002
CF_TEXT = 1


class ClipboardError(Exception):
    pass


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


prototype = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND)
paramflags = ((1, "hWndNewOwner"), )
OpenClipboard = prototype(("OpenClipboard", user32), paramflags)
OpenClipboard.errcheck = bool_errcheck

prototype = ctypes.WINFUNCTYPE(wintypes.BOOL)
CloseClipboard = prototype(("CloseClipboard", user32))
CloseClipboard.errcheck = bool_errcheck

prototype = ctypes.WINFUNCTYPE(wintypes.BOOL)
EmptyClipboard = prototype(("EmptyClipboard", user32))

prototype = ctypes.WINFUNCTYPE(wintypes.HANDLE, wintypes.UINT, wintypes.HANDLE)
paramflags = (1, "uFormat"), (1, "hMem")
SetClipboardData = prototype(("SetClipboardData", user32), paramflags)
SetClipboardData.errcheck = null_errcheck

prototype = ctypes.WINFUNCTYPE(wintypes.LPVOID, wintypes.HGLOBAL)
paramflags = ((1, "hMem"), )
GlobalLock = prototype(("GlobalLock", kernel32), paramflags)
def errcheck(result, func, args):
    if not result:
        raise ctypes.WinError()
    return ctypes.c_char_p(result)
GlobalLock.errcheck = errcheck

prototype = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HGLOBAL)
paramflags = ((1, "hMem"), )
GlobalUnlock = prototype(("GlobalUnlock", kernel32), paramflags)
GlobalUnlock.errcheck = lasterror_errcheck

prototype = ctypes.WINFUNCTYPE(wintypes.HGLOBAL, wintypes.UINT, wintypes.UINT)
paramflags = (1, "uFlags", GMEM_MOVEABLE), (1, "dwBytes")
GlobalAlloc = prototype(("GlobalAlloc", kernel32), paramflags)
GlobalAlloc.errcheck = null_errcheck

prototype = ctypes.WINFUNCTYPE(wintypes.HGLOBAL, wintypes.HGLOBAL)
paramflags = ((1, "hMem"), )
GlobalFree = prototype(("GlobalFree", kernel32), paramflags)
GlobalFree.errcheck = errcheck_expect_null


prototype = ctypes.WINFUNCTYPE(wintypes.HGLOBAL, wintypes.UINT)
paramflags = ((1, "uFormat", CF_TEXT), )
GetClipboardData_ = prototype(("GetClipboardData", user32), paramflags)
GetClipboardData_.errcheck = null_errcheck
# TODO: add a context manager that also allocates and frees the global memory.


@contextlib.contextmanager
def clipboard(hWndNewOwner=NULL):
    try:
        OpenClipboard(hWndNewOwner)
        yield
    finally:
        CloseClipboard()


@contextlib.contextmanager
def global_memory(hGlobalMemory):
    memory = GlobalLock(hGlobalMemory)
    yield memory
    GlobalUnlock(hGlobalMemory)


@contextlib.contextmanager
def global_alloc(flags, size):
    handle = GlobalAlloc(flags, size)

    yield handle

    GlobalFree(handle)


@contextlib.contextmanager
def global_copy(data):
    c_data = ctypes.create_string_buffer(data)
    with global_alloc(GMEM_MOVEABLE, ctypes.sizeof(c_data)) as handle:
        with global_memory(handle) as memory:
            ctypes.memmove(memory, c_data, ctypes.sizeof(c_data))

        yield handle


def Copy(text):
    with clipboard():
        EmptyClipboard()
        # Assuming we are handling ascii
        with global_copy(text) as handle:
            SetClipboardData(CF_TEXT, handle)


def GetClipboardData(format_=CF_TEXT):
    hglb = GetClipboardData_(format_)
    return GlobalMemoryHandle(hglb)


class GlobalMemoryHandle(object):
    def __init__(self, handle):
        self._handle = handle

    @property
    def handle(self):
        return self._handle

    def __enter__(self):
        return GlobalLock(self._handle)

    def __exit__(self, exc_type, exc_val, exc_tb):
        GlobalUnlock(self._handle)


def Paste():
    with clipboard():
        with GetClipboardData(CF_TEXT) as memory:
            return memory.value


if __name__ == '__main__':
    print Paste()
    Copy(Paste() + b"what is this?")
    print Paste()