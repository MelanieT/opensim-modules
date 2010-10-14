from System.Reflection import MethodBase
import clr, os, sys, traceback

logAsm = clr.LoadAssemblyByName('log4net')
log = logAsm.log4net.LogManager.GetLogger(type(MethodBase.GetCurrentMethod().DeclaringType))

from ConfigParser import ConfigParser

def load_or_reload(modulename):
    mod = None
    if sys.modules.has_key(modulename):
        mod = reload(sys.modules[modulename])
    else:
        mod = __import__(modulename, globals(), locals(), [""])

    return mod

def read_ini(inifilename):
    cp = ConfigParser()
    thisdir = os.path.split(os.path.abspath(__file__))[0]
    cp.read([os.path.join(thisdir, inifilename)])
    for s in cp.sections():
        cfdict = dict(cp.items(s))
        try:
            modname, classname = s.rsplit('.', 1)
        except ValueError:
            r.logInfo("bad config section in " + inifilename + ": " + s)
            continue

        yield modname, classname, cfdict

