# Copyright (c) Contributors, http://opensimulator.org/
# See CONTRIBUTORS.TXT for a full list of copyright holders.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the OpenSimulator Project nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE DEVELOPERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
sys.path.append('/usr/lib/python2.6')

import clr
clr.AddReference('OpenSim.Framework')
clr.AddReference('OpenSim.Region.Framework')

import osutil
from osutil import log

# LOADMODS = []
# for modname, classname, cfg in osutil.read_ini("pymodules.ini"):
#     m = osutil.load_or_reload(modname)
#     if m is not None: #loaded succesfully. if not, freshload logged traceback
#         c = getattr(m, classname)
#         LOADMODS.append((c, cfg))

LOADMODS = ["samplemodule"]

from OpenSim.Region.Framework.Interfaces import INonSharedRegionModule

class PyReloader(INonSharedRegionModule):
    upgradable = False
    reginstances = []

    def Initialise(self, scene, configsource):
        self.scene = scene
        self.config = configsource
        scene.AddCommand(self, "py-reload", "py-reload", "...", self.cmd_py_reload)
        log.Info('initialised with' + str(scene))

    def PostInitialise(self):
        log.Info('post-initialise')
    
    def Close(self):
        log.Info('close')

    def getname(self):
        return "MyRegionModule"

    Name = property(getname)

    def isshared(self):
        return False

    IsSharedModule = property(isshared)

    def cmd_py_reload(self, modname, args):
        try:
            self.reload(modname, args)
        except Exception, e:
            log.Error("Python exception on reload")
            import traceback
            traceback.print_exc()
            raise

    def reload(self, modname, args):
        log.Info("closing modules")
        for ri in self.reginstances:
            log.Debug("doing " + str(ri) + " from list of RM instances")
            if ri.Name in self.scene.Modules:
                print "also found in modules, so marking removed"
                ri.removed = True
                print "removing", ri.Name, "from self.scene.Modules"
                self.scene.Modules.Remove(ri.Name)
            else:
                print "not found in modules so not removing"
            ri.Close()

        self.reginstances[:] = []

        print 'reloading modules & looking for region classes'
        regclasses = []
        for mname in LOADMODS:
            osutil.load_or_reload(mname)
            m = sys.modules[mname]
            for name in dir(m):
                o = getattr(m, name)
                if name.startswith('_'):
                    continue
                try:
                    x = issubclass(o, INonSharedRegionModule)
                except TypeError:
                    pass
                else:
                    if x and getattr(o, 'autoload', None):
                        print 'found', name
                        regclasses.append(o)

        print 'instantiating found python modules'
        for klass in regclasses:
            ri = klass()
            ri.Initialise(self.scene, self.config)
            #self.scene.AddModule(ri.Name, ri)
            print "register instance", ri
            self.reginstances.append(ri)
            ri.PostInitialise()
        print 'reload done'

loader = None

def sceneinit(scene, config):
    global loader
    loader = PyReloader()
    loader.Initialise(scene, config)
    loader.PostInitialise()
    loader.cmd_py_reload('', [])
