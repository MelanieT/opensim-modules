import osutil
from OpenSim.Region.Framework.Interfaces import INonSharedRegionModule

print "samplemodule loading"

class HelloWorldModule(INonSharedRegionModule):
    autoload = True

    def Initialise(self, scene, configsource):
        self.scene = scene
        osutil.log.Info("[SAMPLEMODULE] Initialise")

    def PostInitialise(self):
        self.scene.EventManager.OnNewClient += self.newclient_callback

    def getname(self):
        return self.__class__.__name__

    Name = property(getname)

    def callbackwrap(self, fun, suppress=False):
        "makes sure callbacks aren't called for removed modules, and prints tracebacks on failures"
        if self.removed:
            return

        def wrapped(*args, **kw):
            if self.removed:
                return
            try:
                return apply(fun, args, kw)
            except:
                import traceback
                traceback.print_exc()
                if not suppress:
                    raise

        return wrapped

    def Close(self):
        osutil.log.Info("[SAMPLEMODULE] Closing")

    def newclient_callback(self, clientview):
        osutil.log.Info("[SAMPLEMODULE] new client: " + str(clientview.AgentId))

