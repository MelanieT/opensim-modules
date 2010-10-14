import osutil
from OpenSim.Region.Framework.Interfaces import INonSharedRegionModule

print "samplemodule loading"

class HelloWorldModule(INonSharedRegionModule):
    autoload = True

    def Initialise(self, configsource):
        osutil.log.Info("[SAMPLEMODULE] Initialise")

    def AddRegion(self, scene):
        osutil.log.Info("[SAMPLEMODULE] AddRegion called")
        try:
            #INonSharedRegionModule.AddRegion(self, scene)
            self.scene = scene
            osutil.log.Info("[SAMPLEMODULE] hooking OnNewClient")
            scene.EventManager.OnNewClient += self.newclient_callback
        except:
            import traceback
            traceback.print_exc()

    def getname(self):
        return self.__class__.__name__

    Name = property(getname)

    def Close(self):
        osutil.log.Info("[SAMPLEMODULE] Closing")

    def newclient_callback(self, clientview):
        osutil.log.Info("[SAMPLEMODULE] new client: " + str(clientview.AgentId))

