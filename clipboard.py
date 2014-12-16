import contextlib
import ctypes

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


def OpenClipboard(hWndNewOwner=NULL):
    hWndNewOwner = HWND(hWndNewOwner)
    success = user32.OpenClipboard(hWndNewOwner)
    if not success:
        raise ClipboardError("Cannot Open Clipboard")


@contextlib.contextmanager
def clipboard(hWndNewOwner=NULL):
    try:
        OpenClipboard(hWndNewOwner)
        yield
    finally:
        CloseClipboard()


def CloseClipboard():
    success = user32.CloseClipboard()
    if not success:
        raise ClipboardError("Cannot close clipboard")


def EmptyClipboard():
    return user32.EmptyClipboard()


def global_lock(memory_handle):
    memory = kernel32.GlobalLock(memory_handle)
    if not memory:
        raise MemoryError("Failed locking global memory")
    return ctypes.c_char_p(memory)


def global_unlock(hGlobalMemory):
    is_locked = kernel32.GlobalUnlock(hGlobalMemory)
    # No need to check return value??
    # if is_locked:
    # raise MemoryError("memory is still locked.")


# TODO: add a context manager that also allocates and frees the global memory.



@contextlib.contextmanager
def global_memory(hGlobalMemory):
    memory = global_lock(hGlobalMemory)
    yield memory
    global_unlock(hGlobalMemory)


@contextlib.contextmanager
def global_alloc(flags, size):
    handle = kernel32.GlobalAlloc(flags, size)
    if not handle:
        # TODO: use GetLastError() here.
        raise MemoryError("Allocation failed.")

    yield GlobalMemoryHandle(handle)

    kernel32.GlobalFree(handle)


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
            user32.SetClipboardData(CF_TEXT, handle)


def GetClipboardData(format_=CF_TEXT):
    hglb = user32.GetClipboardData(format_)
    if not hglb:
        raise ClipboardError("Cannot get data.")
    return GlobalMemoryHandle(hglb)


class GlobalMemoryHandle(object):
    def __init__(self, handle):
        self._handle = handle

    @property
    def handle(self):
        return self._handle

    def __enter__(self):
        return global_lock(self._handle)

    def __exit__(self, exc_type, exc_val, exc_tb):
        global_unlock(self._handle)


def Paste():
    with clipboard():
        with GetClipboardData(CF_TEXT) as memory:
            return memory.value


if __name__ == '__main__':
    print Paste()
    Copy(Paste() + b"what is this?")
    print Paste()