/*
 * Copyright (c) Contributors, http://opensimulator.org/
 * See CONTRIBUTORS.TXT for a full list of copyright holders.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *     * Redistributions of source code must retain the above copyright
 *       notice, this list of conditions and the following disclaimer.
 *     * Redistributions in binary form must reproduce the above copyright
 *       notice, this list of conditions and the following disclaimer in the
 *       documentation and/or other materials provided with the distribution.
 *     * Neither the name of the OpenSimulator Project nor the
 *       names of its contributors may be used to endorse or promote products
 *       derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE DEVELOPERS ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE CONTRIBUTORS BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

using System;
using System.Collections.Generic;
using System.Reflection;
using System.IO;

using log4net;
using Nini.Config;
using OpenMetaverse;
using Mono.Addins;

using OpenSim.Framework;
using OpenSim.Framework.Console;
using OpenSim.Region.Framework.Interfaces;
using OpenSim.Region.Framework.Scenes;

[assembly: Addin("Simrot.Module", OpenSim.VersionInfo.VersionNumber + "0.1")]
[assembly: AddinDependency("OpenSim.Region.Framework", OpenSim.VersionInfo.VersionNumber)]
[assembly: AddinDescription("Rotate sims incl. terrain.")]
[assembly: AddinAuthor("Melanie Thielker")]

namespace Simrot
{
    [Extension(Path = "/OpenSim/RegionModules", NodeName = "RegionModule", Id = "Simrot")]
    public class SimrotModule : INonSharedRegionModule
    {
        private static readonly ILog m_log = LogManager.GetLogger(
                MethodBase.GetCurrentMethod().DeclaringType);

        private enum Direction
        {
            left = 90,
            right = 270,
        }

        Scene m_Scene;
		IConfigSource m_Config;
		
        #region Region Module interface

        public void Initialise(IConfigSource config)
        {
            m_log.Info("[SIMROT] Module loaded");
			m_Config = config;
        }

        public void AddRegion(Scene scene)
        {
            m_Scene = scene;
        }

        public void RegionLoaded(Scene scene)
        {
            m_Scene.AddCommand(this, "region rotate",
                               "region rotate <direction>",
                               "Rotate entire region in the given direction",
                               HandleRotate);
        }

        public void RemoveRegion(Scene scene)
        {
        }

		public void Close()
        {
        }

        public string Name
        {
            get { return "SimrotModule"; }
        }

        public Type ReplaceableInterface
        {
            get { return null; }
        }

        #endregion

        private void HandleRotate(string module, string[] cmd)
        {
            if (!(MainConsole.Instance.ConsoleScene is Scene))
                return;

            if ((Scene)MainConsole.Instance.ConsoleScene != m_Scene)
                return;

            if (cmd.Length < 3)
            {
                MainConsole.Instance.Output("Error: missing direction");
                return;
            }

            Direction dir;

            try
            {
                dir = (Direction)Enum.Parse(typeof(Simrot.SimrotModule.Direction), cmd[2]);
            }
            catch (Exception)
            {
                MainConsole.Instance.Output("Error: dorection must be left or right");
                return;
            }

            Quaternion q = Quaternion.CreateFromEulers(0, 0, (float)((float)((int)dir) * Math.PI / 180.0));
            Vector3 vc = new Vector3(128.0f, 128.0f, 128.0f);

            m_Scene.ForEachSOG(delegate (SceneObjectGroup g)
            {
                if (g.IsAttachment)
                    return;

                g.RootPart.UpdateRotation(q * g.GroupRotation);
                Vector3 v = g.AbsolutePosition - vc;
                g.AbsolutePosition = vc + v * q;
            });

            double[,] map = m_Scene.Heightmap.GetDoubles();
            double[,] newMap =
                    new double[Constants.RegionSize, Constants.RegionSize];

            if (dir == Direction.left)
            {
                for (int x = 0 ; x < Constants.RegionSize ; ++x)
                {
                    for (int y = 0 ; y < Constants.RegionSize ; ++y)
                        newMap[Constants.RegionSize - y - 1, x] = map[x, y];
                }
            }
            else
            {
                for (int x = 0 ; x < Constants.RegionSize ; ++x)
                {
                    for (int y = 0 ; y < Constants.RegionSize ; ++y)
                        newMap[y, Constants.RegionSize - x - 1] = map[x, y];
                }
            }
            for (int x = 0 ; x < Constants.RegionSize ; ++x)
            {
                for (int y = 0 ; y < Constants.RegionSize ; ++y)
                    m_Scene.Heightmap[x, y] = newMap[x, y];
            }

            ITerrainModule tm = m_Scene.RequestModuleInterface<ITerrainModule>();
            if (tm == null)
            {
                MainConsole.Instance.Output("No terrain modules installed, not sending terrain");
                return;
            }

            tm.UndoTerrain(m_Scene.Heightmap);
            tm.TaintTerrain();

            MainConsole.Instance.Output("Rotation done");
        }
    }
}
