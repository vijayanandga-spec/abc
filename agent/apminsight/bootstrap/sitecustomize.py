import os
import sys
import time

debug = os.environ.get("APM_DEBUG", False)

# Python version
PYTHON_VERSION = sys.version_info[:2]


def log(text, *args, **kwargs):
    if debug:
        text = text % args
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sys.stdout.write("APM_INSIGHT_PYTHON: %s (%d) - %s\n" % (timestamp, os.getpid(), text))
        sys.stdout.flush()


log("python_version %s" % str(PYTHON_VERSION))

try:
    boot_directory = os.path.dirname(__file__)
    log("boot_directory(%s)", boot_directory)

    # Check for and import original sitecustomize normally used
    path = list(sys.path)
    log("sys.path = %r", sys.path)
    if boot_directory in path:
        index = path.index(boot_directory)
        del path[index]

    if PYTHON_VERSION < (3, 0):
        import imp

        module_spec = imp.find_module("sitecustomize", path)
        if module_spec is not None:
            log("Additional sitecustomize found = %r", str(module_spec))
            # loads the module code from a compiled bytecode file (.pyc file) or an already loaded module object.
            imp.load_module("sitecustomize", *module_spec)
    else:
        from importlib.machinery import PathFinder

        module_spec = PathFinder.find_spec("sitecustomize", path=path)
        if module_spec is not None:
            log("Additional sitecustomize found = %r", str(module_spec))
            module_spec.loader.load_module("sitecustomize")
except Exception as e:
    log("Error while checking for additional sitecustomize files %s", str(e))

try:
    if PYTHON_VERSION >= (3, 5):
        import apminsight

        apminsight.initialize_agent()
    else:
        print("[ERROR] apm module works only for python version greater then 3.5")
        print("APM Python Agent is Not initiated")
        print("Resuming normal Execution of the code")

except Exception as exc:
    print("Error while installing Agent ", str(exc))
    import traceback
    traceback.print_exc()
