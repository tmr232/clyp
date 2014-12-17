import contextlib
import ctypes
from ctypes import wintypes

from pywrap import wrap_winapi, Parameter, Errcheck

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Types
NULL = 0

GMEM_MOVEABLE = 0x0002
CF_TEXT = 1

OpenClipboard = wrap_winapi(name="OpenClipboard",
                            library=user32,
                            restype=wintypes.BOOL,
                            params=[
                                Parameter("hWndNewOwner", wintypes.HWND, default=0)
                            ],
                            errcheck=Errcheck.expect_true)

CloseClipboard = wrap_winapi(name="CloseClipboard",
                             library=user32,
                             restype=wintypes.BOOL,
                             params=[],
                             errcheck=Errcheck.expect_true)

EmptyClipboard = wrap_winapi(name="EmptyClipboard",
                             library=user32,
                             restype=wintypes.BOOL,
                             params=[],
                             errcheck=Errcheck.expect_true)

SetClipboardData = wrap_winapi(name="SetClipboardData",
                               library=user32,
                               restype=wintypes.BOOL,
                               params=[
                                   Parameter("uFormat", wintypes.UINT),
                                   Parameter("hMem", wintypes.HANDLE)
                               ],
                               errcheck=Errcheck.expect_not_null)

GetClipboardData = wrap_winapi(name="GetClipboardData",
                               library=user32,
                               restype=wintypes.HGLOBAL,
                               params=[
                                   Parameter("uFormat", wintypes.UINT, default=CF_TEXT)
                               ],
                               errcheck=Errcheck.expect_not_null)


def globallock_errcheck(result, func, args):
    if not result:
        raise ctypes.WinError()
    return ctypes.c_char_p(result)


GlobalLock = wrap_winapi(name="GlobalLock",
                         library=kernel32,
                         restype=wintypes.LPVOID,
                         params=[
                             Parameter("hMem", wintypes.HGLOBAL)
                         ],
                         errcheck=globallock_errcheck)

GlobalUnlock = wrap_winapi(name="GlobalUnlock",
                           library=kernel32,
                           restype=wintypes.BOOL,
                           params=[
                               Parameter("hMem", wintypes.HGLOBAL)
                           ],
                           errcheck=Errcheck.expect_no_error)

GlobalAlloc = wrap_winapi(name="GlobalAlloc",
                          library=kernel32,
                          restype=wintypes.HGLOBAL,
                          params=[
                              Parameter("uFlags", wintypes.UINT, default=GMEM_MOVEABLE),
                              Parameter("dwBytes", wintypes.UINT)
                          ],
                          errcheck=Errcheck.expect_not_null)

GlobalFree = wrap_winapi(name="GlobalFree",
                         library=kernel32,
                         restype=wintypes.HGLOBAL,
                         params=[
                             Parameter("hMem", wintypes.HGLOBAL)
                         ],
                         errcheck=Errcheck.expect_null)


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