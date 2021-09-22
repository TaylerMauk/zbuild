'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import os
from pathlib import Path
from typing import Any, Callable

from argsd import ArgHelper
from constants import ResultCode
from services.compiler import CompilerService
from services.configuration import ConfigurationService
from services.output import OutputService

class Application():
    def __init__(self):
        self.config = None
        self.output = None
        self.argHelper = ArgHelper()
        self.actions: list[tuple[Callable, Any]] = []

        self.InitArgs()

    def Run(self):
        os.chdir(Path(__file__).parent.absolute())
        self.config = ConfigurationService()
        if not self.RunStartupChecks() == ResultCode.SUCCESS:
            self.Quit(1)

        self.GetAvailableBuildConfigs()
        self.argHelper.AppendToHelpMessage(self.GetDynamicHelpMessageContent())
        resultCode, self.actions = self.argHelper.ParseArgs()
        if not resultCode == ResultCode.SUCCESS:
            self.Quit(resultCode)
        
        os.chdir(self.config.GetProjectRoot())
        self.output = OutputService(self.config.GetLogPath())
        self.output.SendInfoPrintOnly(f"Logging to file '{self.config.GetLogPath()}'")
        self.output.SendInfo(f"Project root directory detected as '{self.config.GetProjectRoot()}'")

        self.ExecuteActions()
        self.Quit()

    def Quit(self, code: int = ResultCode.SUCCESS):
        if self.output is None:
            exit(0 if code == ResultCode.SUCCESS else 1)

        exitCode = None
        msg = f"Operation exited with code 0x{code:04x}"
        if code == ResultCode.SUCCESS:
            self.output.SendInfoLogOnly(msg)
            exitCode = 0
        else:
            self.output.SendWarningLogOnly(msg)
            exitCode = code // code

        self.output.Close()
        exit(exitCode)

    def RunStartupChecks(self):
        lastResultCode = self.config.CheckConfigDir()
        if not lastResultCode == ResultCode.SUCCESS:
            print(f"Could not find the configuration directory '{self.config.GetConfigDir()}'")
            return lastResultCode

        lastResultCode = self.config.LoadRootConfig()
        if not lastResultCode == ResultCode.SUCCESS:
            print(f"Could not load the root configuration file {self.config.GetRootConfigFilename()}")
            return lastResultCode

        lastResultCode = self.config.LoadRootConfig()
        if not self.config.CheckRootConfig() == ResultCode.SUCCESS:
            print("The root configuration is not valid")
            return lastResultCode

        lastResultCode = self.config.LoadRootConfig()
        if not self.config.FindProjectRoot() == ResultCode.SUCCESS:
            print(f"Could not find {self.config.GetRootLocatorName()} in your project file tree")
            return lastResultCode

        return ResultCode.SUCCESS

    def GetAvailableBuildConfigs(self):
        buildConfigs = []
        buildConfigFileExt = self.config.GetBuildFileExt()
        for configFile in self.config.GetConfigDir().iterdir():
            if not configFile.is_file():
                continue
            
            filename = configFile.parts[-1]
            if not filename.endswith(buildConfigFileExt):
                continue

            buildConfigName = filename[:filename.rindex(buildConfigFileExt) - 1]
            buildConfigs.append(buildConfigName)

        return buildConfigs

    def GetDynamicHelpMessageContent(self):
        availableBuildConfigs = self.GetAvailableBuildConfigs()

        msg = "Available Build Configurations:\n"
        for n in availableBuildConfigs:
            msg += f"    {n}\n"
        
        return msg

    def InitArgs(self):
        self.argHelper.AddArg(
            shortName = None,
            longName  = "update",
            helpInfo  = "update to the latest release",
            group     = 0,
            isSwitch  = True,
            action    = self.ActionUpdate
        )

        self.argHelper.AddArg(
            shortName = None,
            longName  = "repair",
            helpInfo  = "download a fresh copy of the current version",
            group     = 0,
            isSwitch  = True,
            action    = self.ActionRepair
        )

        self.argHelper.AddArg(
            shortName = None,
            longName  = "init",
            helpInfo  = "initialize zbuild workspace",
            group     = 0,
            isSwitch  = True,
            action    = self.ActionInitWorkspace
        )

        self.argHelper.AddArg(
            shortName = "b",
            longName  = "build",
            helpInfo  = "build given configuration",
            group     = 1,
            varName   = "build_name",
            action    = self.ActionInitWorkspace
        )

        self.argHelper.AddArg(
            shortName = "r",
            longName  = "run",
            helpInfo  = "run given configuration, will build first if executable not found",
            group     = 1,
            varName   = "build_name",
            action    = self.ActionInitWorkspace
        )

        self.argHelper.AddArg(
            shortName = "n",
            longName  = "new",
            helpInfo  = "generate template for new configuration",
            group     = 1,
            varName   = "name",
            action    = self.ActionInitWorkspace
        )

    def ExecuteActions(self):
        # TODO: respect result codes
        for action, param in self.actions:
            if param is None:
                action()
            else:
                action(param)
        return ResultCode.SUCCESS

    def ActionInitWorkspace(self):
        self.output.SendInfo("Workspace initialization requested")
        return ResultCode.ERR_NOT_IMPLEMENTED
        
    def ActionRepair(self):
        self.output.SendInfo("Repair requested")
        return ResultCode.ERR_NOT_IMPLEMENTED
        
    def ActionUpdate(self):
        self.output.SendInfo("Update requested")
        return ResultCode.ERR_NOT_IMPLEMENTED
        
    def ActionBuild(self):
        self.output.SendInfo("Build requested")

        # TODO: Load build config
        CompilerService(self.config, self.output).Compile()

        return ResultCode.ERR_NOT_IMPLEMENTED
