"""Read-only resource guards and priority for explicitly invoked benchmarks."""
import ctypes
import os


def headroom():
    if os.name != "nt":
        raise RuntimeError("This workstation protocol needs a supported commit-headroom probe")
    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [(n, ctypes.c_ulonglong) for n in
            ("totalRam", "availableRam", "totalCommit", "availableCommit", "totalVirtual", "availableVirtual", "extended")]
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError("Cannot establish memory headroom")
    return {"ramGiB": memory.availableRam / 2**30, "commitGiB": memory.availableCommit / 2**30}


def guard(*, large_model=False):
    value = headroom()
    floor = 20 if large_model else 8
    if min(value.values()) < floor:
        raise RuntimeError(f"Resource gate: need {floor} GiB RAM/commit headroom; observed {value}")
    return value


def benchmark_priority(threads):
    if threads not in (1, 2):
        raise ValueError("Current shared-host authorization caps benchmark threads at two")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = str(threads)
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    if os.name == "nt":
        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise OSError("Could not set below-normal benchmark priority")
