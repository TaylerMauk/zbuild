'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import json
import os
from pathlib import Path

from constants import Configuration, KeyNames, ReservedValues, ResultCode

class ConfigurationService:
    def __init__(self):
        self.configRoot = Path(os.getcwd()).resolve()
        self.projectRoot = None
        self.rootData = None

        self.buildName = None
        self.buildData = None
        self.buildSharedResources = None

        self.buildStepNames = []
        self.buildStepNumber = -1
        self.buildStepName = ""
        self.buildStepData = None

# Root Configuration
################################################################################

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
        
    def GetToolchain(self):
        return str(self.rootData[KeyNames.Root.Toolchain.ROOT])

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

            if not self.CheckRootConfig() == ResultCode.SUCCESS:
                return ResultCode.ERR_CONFIG_INVALID
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

# Build Configuration
################################################################################
        
    def GetBuildName(self):
        return str(self.buildName)

    def GetBuildFileExt(self):
        return Configuration.Build.Files.EXTENSION

    def LoadBuildConfig(self, buildName: str):
        buildFilePath = self.GetConfigDir() / f"{buildName}.{Configuration.Build.Files.EXTENSION}"
        if buildFilePath.exists():
            with open(buildFilePath, "r") as f:
                self.buildData = json.load(f)

            if not self.CheckBuildConfig() == ResultCode.SUCCESS:
                return ResultCode.ERR_CONFIG_INVALID

            self.buildName = buildName
            self.buildStepNumber = 0
            self.buildStepNames = list(self.buildData[KeyNames.Build.Steps.ROOT].keys())
            self.buildSharedResources = self.buildData[KeyNames.Build.SharedRecources.ROOT]
            return ResultCode.SUCCESS
        
        return ResultCode.ERR_FILE_NOT_FOUND

    def CheckBuildConfig(self):
        if not self.buildData.keys() & { KeyNames.Build.SharedRecources.ROOT, KeyNames.Build.Steps.ROOT }:
            return ResultCode.ERR_CONFIG_INVALID
        return ResultCode.SUCCESS

# Build Step Configuration
################################################################################

    def LoadNextBuildStep(self):
        if self.buildStepNumber == len(self.buildStepNames):
            return ResultCode.WRN_NO_VALUE

        self.buildStepName = self.buildStepNames[self.buildStepNumber]
        self.buildStepData = self.buildData[KeyNames.Build.Steps.ROOT][self.buildStepName]
        self.buildStepNumber += 1
        return ResultCode.SUCCESS

    def GetBuildStepIncludeDirectories(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.INCLUDE_DIRECTORIES)

    def GetBuildStepSourceDirectories(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.SOURCE_DIRECTORIES)

    def GetBuildStepSourceExtension(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.SOURCE_FILE_EXTENSTION)

    def GetBuildStepHeaderExtension(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.HEADER_FILE_EXTENSTION)

    def GetBuildStepExecutableName(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.EXECUTABLE_NAME)

    def __GetBuildStepValue(self, keyName: str):
        if not keyName in self.buildStepData:
            return (ResultCode.WRN_NO_VALUE, None)

        dataValue = self.buildStepData[keyName]

        if not dataValue == ReservedValues.Configuration.Build.SharedResource.LOOKUP:
            return (ResultCode.SUCCESS, dataValue)

        if keyName in self.buildSharedResources:
            sharedResource = self.buildSharedResources[keyName]
            sharedResourceAppliesTo = sharedResource[KeyNames.Build.SharedRecources.APPLIES_TO]

            if sharedResourceAppliesTo == ReservedValues.Configuration.Build.SharedResource.APPLIES_TO_ALL or self.buildStepName in sharedResourceAppliesTo:
                return (ResultCode.SUCCESS, sharedResource[KeyNames.Build.SharedRecources.VALUE])
            else:
                return (ResultCode.WRN_NO_VALUE, None)
