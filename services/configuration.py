'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import json
import os
from pathlib import Path

from constants import Configuration, KeyNames, ResultCode

class ConfigurationService:
    def __init__(self):
        self.configRoot = Path(os.getcwd()).resolve()
        self.projectRoot = None
        self.rootData = None

        self.buildName = None
        self.buildStepNumber = -1
        self.buildStepNames = []
        self.buildData = None

        self.runData = None

    def GetConfigDir(self):
        return self.configRoot / Configuration.Files.DIR_NAME

    def GetRootConfigFilename(self):
        return Configuration.Root.FILE_NAME
        
    def GetRootLocatorName(self):
        return Configuration.App.RootLocator.NAME

    def GetProjectRoot(self):
        return self.projectRoot

    def GetExecutableOutputDir(self):
        return Path(self.projectRoot / self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.EXECUTABLE])

    def GetObjectOutputDir(self):
        return Path(self.projectRoot / self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.OBJECT])

    def GetDebugSymbolsOutputDir(self):
        return Path(self.projectRoot / self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.DEBUG_SYMBOLS])

    def GetLogOutputDir(self):
        return Path(self.projectRoot / self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.LOG])

    def GetCompilerOutputDirs(self):
        return [
            self.GetExecutableOutputDir(),
            self.GetDebugSymbolsOutputDir(),
            self.GetObjectOutputDir()
        ]
    
    def GetLogPath(self):
        return self.GetLogOutputDir() / f"{Configuration.App.NAME}.log"
    
    def GetArgsdPath(self):
        return self.GetConfigDir() / Configuration.App.Argsd.NAME
        
    def GetToolchain(self):
        return str(self.rootData[KeyNames.Root.Toolchain.ROOT])
        
    def GetBuildName(self):
        return str(self.buildName)

    def GetBuildFileExt(self):
        return Configuration.Build.Files.EXTENSION

    def GetNextBuildStep(self):
        if self.buildStepNumber == len(self.buildStepNames):
            return None

        buildStepName = self.buildStepNames[self.buildStepNumber]
        buildStepData = self.buildData[KeyNames.Build.Steps.ROOT][buildStepName]
        self.buildStepNumber += 1
        return buildStepData

    def CheckConfigDir(self):
        with self.GetConfigDir() as configDirPath:
            if configDirPath.exists():
                return ResultCode.SUCCESS
        
        return ResultCode.ERR_DIR_NOT_FOUND

    def LoadRootConfig(self):
        rootConfigPath = Path(Configuration.Files.DIR_NAME) / Path(Configuration.Root.FILE_NAME)
        if rootConfigPath.exists():
            with open(rootConfigPath, "r") as f:
                self.rootData = json.load(f)
            
            return ResultCode.SUCCESS
        
        return ResultCode.ERR_FILE_NOT_FOUND

    def CheckRootConfig(self):
        if not self.rootData.keys() & { KeyNames.Root.OutputDirectories.ROOT, KeyNames.Root.Platform.ROOT, KeyNames.Root.Toolchain.ROOT }:
            return ResultCode.ERR_CONFIG_INVALID
        
        return ResultCode.SUCCESS

    def FindProjectRoot(self):
        dir = Path(os.getcwd())
        isRootFound = False

        # Search ancestor directories for root locator
        while not isRootFound and dir.parent != dir:
            for p in dir.iterdir():
                if p.is_file() and p.name == Configuration.App.RootLocator.NAME:
                    self.projectRoot = Path(dir).resolve()
                    isRootFound = True

            dir = dir.parent

        if isRootFound:
            return ResultCode.SUCCESS
        return ResultCode.ERR_FILE_NOT_FOUND

    def LoadBuildConfig(self, buildName: str):
        buildFilePath = self.GetConfigDir() / f"{buildName}.{Configuration.Build.Files.EXTENSION}"
        if buildFilePath.exists():
            with open(buildFilePath, "r") as f:
                self.buildData = json.load(f)

            self.buildName = buildName
            self.buildStepNumber = 0
            self.buildStepNames = list(self.buildData[KeyNames.Build.Steps.ROOT].keys())
            return ResultCode.SUCCESS
        
        return ResultCode.ERR_FILE_NOT_FOUND

    def CheckBuildConfig(self):
        return ResultCode.ERR_NOT_IMPLEMENTED

    def ReadBuildKey(self, keyName: str):
        if not keyName in self.buildData:
            return None
        return self.buildData[keyName]

    def ReadRootKey(self, keyName: str):
        if not keyName in self.rootData:
            return None
        return self.rootData[keyName]

    def ReadRunKey(self, keyName: str):
        if not keyName in self.data:
            return None
        return self.runData[keyName]
