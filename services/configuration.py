'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import json
import os
from pathlib import Path

from constants import Configuration, KeyNames, ReservedValues, ResultCode

class PathType():
    ABSOLUTE = 0
    RELATIVE = 1

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
        
    def GetTargetPlatform(self):
        return self.rootData[KeyNames.Root.Platform.ROOT]

    def GetTargetOutputDir(self, pathType: PathType):
        relativePath = self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.TARGET]

        if pathType == PathType.RELATIVE:
            return Path(relativePath)
        return Path(self.projectRoot / relativePath)

    def GetObjectOutputDir(self, pathType: PathType):
        relativePath = self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.OBJECT]

        if pathType == PathType.RELATIVE:
            return Path(relativePath)
        return Path(self.projectRoot / relativePath)

    def GetDebugSymbolsOutputDir(self, pathType: PathType):
        relativePath = self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.DEBUG_SYMBOLS]

        if pathType == PathType.RELATIVE:
            return Path(relativePath)
        return Path(self.projectRoot / relativePath)

    def GetLogOutputDir(self, pathType: PathType):
        relativePath = self.rootData[KeyNames.Root.OutputDirectories.ROOT][KeyNames.Root.OutputDirectories.LOG]

        if pathType == PathType.RELATIVE:
            return Path(relativePath)
        return Path(self.projectRoot / relativePath)

    def GetCompilerOutputDirs(self, pathType: PathType):
        return [
            self.GetTargetOutputDir(pathType),
            self.GetDebugSymbolsOutputDir(pathType),
            self.GetObjectOutputDir(pathType)
        ]
    
    def GetLogPath(self, pathType: PathType):
        return self.GetLogOutputDir(pathType) / f"{Configuration.App.NAME}.log"
        
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
            self.buildStepNumber = -1
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
        if self.buildStepNumber == len(self.buildStepNames) - 1:
            return ResultCode.WRN_NO_VALUE

        self.buildStepNumber += 1
        self.buildStepName = self.buildStepNames[self.buildStepNumber]
        self.buildStepData = self.buildData[KeyNames.Build.Steps.ROOT][self.buildStepName]
        return ResultCode.SUCCESS

    def GetBuildStepName(self):
        return self.buildStepName

    def GetBuildStepDefines(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.DEFINES)

    def GetBuildStepIncludeDirectories(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.INCLUDE_DIRECTORIES)

    def GetBuildStepSourceDirectories(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.SOURCE_DIRECTORIES)

    def GetBuildStepSourceExtension(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.SOURCE_FILE_EXTENSTION)

    def GetBuildStepHeaderExtension(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.HEADER_FILE_EXTENSTION)

    def GetBuildStepTargetName(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.TARGET_NAME)

    def GetBuildStepTargetType(self):
        return self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.TARGET_TYPE)

    def GetBuildStepDynamicSharedLibraries(self):
        return self.__GetBuildStepSharedLibraries(KeyNames.Build.Steps.Detail.SharedLibraries.DYNAMIC)

    def GetBuildStepStaticSharedLibraries(self):
        return self.__GetBuildStepSharedLibraries(KeyNames.Build.Steps.Detail.SharedLibraries.STATIC)

    def __GetBuildStepValue(self, keyName: str):
        if not keyName in self.buildStepData and not keyName in self.buildSharedResources:
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

    def __GetBuildStepSharedLibraries(self, libType: str):
        resultCode, libData = self.__GetBuildStepValue(KeyNames.Build.Steps.Detail.SharedLibraries.ROOT)
        if not resultCode == ResultCode.SUCCESS:
            return (resultCode, None)

        sharedLibs = []

        if ReservedValues.Configuration.Build.Target.Platform.ALL in libData:
            allPlatformLibs = libData[ReservedValues.Configuration.Build.Target.Platform.ALL]

            if libType in allPlatformLibs:
                for lib in allPlatformLibs[libType]:
                    sharedLibs.append(lib)

        targetPlatform = self.GetTargetPlatform()
        if targetPlatform in libData:
            targetPlatformLibs = libData[targetPlatform]
            
            if libType in targetPlatformLibs:
                for lib in targetPlatformLibs[libType]:
                    sharedLibs.append(lib)

        return (ResultCode.SUCCESS, sharedLibs)
