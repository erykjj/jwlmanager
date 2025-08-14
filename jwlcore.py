#!/usr/bin/env python3

"""
  Bridge to jwlCore libs

  MIT License:  Copyright (c) 2025 Eryk J.

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
"""

import ctypes, os, platform, sys

def _platform_lib_name(base="jwlCore"):
    arch = platform.machine().lower()
    sysname = sys.platform

    if arch in ("x86_64", "amd64"):
        arch = "x86_64" if not sysname.startswith("win") else "amd64"
    elif arch in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        raise OSError(f"Unsupported architecture: {arch}")

    if sysname.startswith("linux"):
        return f"lib{base}-{arch}.so"
    elif sysname == "darwin":
        return f"lib{base}-{arch}.dylib"
    elif sysname == "win32":
        return f"{base}-{arch}.dll"
    else:
        raise OSError(f"Unsupported platform: {sysname}")

def _candidate_dirs():
    env = os.environ.get("JWLCORE_PATH")
    if env:
        yield env
    # PyInstaller
    if hasattr(sys, "_MEIPASS"):
        yield sys._MEIPASS
        yield os.path.join(sys._MEIPASS, "libs")
    # Nuitka / normal
    base = os.path.dirname(getattr(sys, "executable", "") if getattr(sys, "frozen", False) else __file__)
    yield base
    yield os.path.join(base, "libs")

def _try_add_win_search_path(path):
    if os.name == "nt":
        try:
            os.add_dll_directory(path)
        except Exception:
            pass

def _find_lib():
    name = _platform_lib_name()
    for d in _candidate_dirs():
        p = os.path.join(d, name)
        if os.path.exists(p):
            _try_add_win_search_path(os.path.dirname(p))
            return p
    raise FileNotFoundError(f"Could not find {name} in any of: "
                            f"{', '.join(dict.fromkeys(_candidate_dirs()))}")

def _load_lib():
    path = _find_lib()
    kwargs = {}
    if hasattr(os, "RTLD_LOCAL") and sys.platform != "win32":
        kwargs["mode"] = os.RTLD_LOCAL
    return ctypes.CDLL(path, **kwargs)

lib = _load_lib()

CALLBACKTYPE = ctypes.CFUNCTYPE(None, ctypes.c_int)

lib.setProgressCallback.argtypes = [CALLBACKTYPE]
lib.setProgressCallback.restype  = None

lib.mergeDatabase.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.mergeDatabase.restype  = ctypes.c_int

lib.getLastResult.argtypes = []
lib.getLastResult.restype  = ctypes.c_char_p

lib.getCoreVersion.argtypes = []
lib.getCoreVersion.restype  = ctypes.c_char_p

# Python wrappers
def merge_database(path1: str, path2: str) -> int:
    return lib.mergeDatabase(path1.encode("utf-8"), path2.encode("utf-8"))

def get_last_result() -> str | None:
    p = lib.getLastResult()
    return p.decode("utf-8") if p else None

def get_core_version() -> str | None:
    p = lib.getCoreVersion()
    return p.decode("utf-8") if p else None
