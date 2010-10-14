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

class PyReloader:
    upgradable = False
    reginstances = []

    def Initialise(self, xpymod, configsource):
        self.config = configsource
        log.Info('[PYMODLOADER] initialised')
        xpymod.OnAddRegion += self.handleaddregion
        xpymod.OnRegionLoaded += self.handleregionloaded
        self.xpymod = xpymod
        self.load()

    def handleaddregion(self, scene):
        log.Info("handleaddregion called")
        scene.AddCommand(self.xpymod, "py-reload", "py-reload", "...", self.cmd_py_reload)
        self.scene = scene
        for rm in self.reginstances:
            log.Info("adding scene %s to region module %s" % (scene, rm))
            scene.AddRegionModule(rm.Name, rm)
            rm.AddRegion(scene)

    def handleregionloaded(self, scene):
        for rm in self.reginstances:
            rm.RegionLoaded(scene)

    def cmd_py_reload(self, modname, args):
        try:
            self.reload()
        except Exception, e:
            log.Error("Python exception on reload")
            import traceback
            traceback.print_exc()
            raise

    def load(self):
        print 'loading modules & looking for region classes'
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
            ri.Initialise(self.config)
            print "register instance", ri
            self.reginstances.append(ri)
        print 'load done'

    def reload(self):
        log.Info("closing modules")
        for ri in self.reginstances:
            log.Debug("doing " + str(ri) + " from list of RM instances")
            if ri.Name in self.scene.RegionModules:
                print "also found in modules, so marking removed"
                ri.removed = True
                print "removing", ri.Name, "from self.scene.Modules"
                self.scene.RemoveRegionModule(ri.Name)
            else:
                print "not found in modules so not removing"
            ri.RemoveRegion(self.scene)
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
            ri.Initialise(self.config)
            print "register instance", ri
            self.reginstances.append(ri)
            self.scene.AddRegionModule(ri.Name, ri)
            ri.AddRegion(self.scene)
            ri.RegionLoaded(self.scene)
        print 'reload done'

loader = None

def init(xpymod, config):
    log.Info("[PYMODLOADER] init called")
    global loader
    loader = PyReloader()
    loader.Initialise(xpymod, config)
    log.Info("[PYMODLOADER] init finished")
