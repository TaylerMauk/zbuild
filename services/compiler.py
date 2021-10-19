'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import os
from pathlib import Path
import subprocess

from constants import ReservedValues, ResultCode
from services.configuration import ConfigurationService, PathType
from services.output import OutputService

class CompilerService:
    def __init__(self, config: ConfigurationService, output: OutputService):
        self.output = output
        self.config = config
        self.buildName = self.config.GetBuildName()
        self.errorIndicator = None
        self.warningIndicator = None
        self.lastResultCode = ResultCode.SUCCESS

    def Compile(self):
        dir = self.config.GetTargetOutputDir(PathType.ABSOLUTE) / self.buildName
        if dir.exists():
            self.__ClearDirTree(dir)
        else:
            os.makedirs(dir)

        os.makedirs(self.config.GetObjectOutputDir(PathType.ABSOLUTE) / self.buildName, exist_ok = True)
        os.makedirs(self.config.GetDebugSymbolsOutputDir(PathType.ABSOLUTE) / self.buildName, exist_ok = True)
        
        toolchain = self.config.GetToolchain()
        self.output.SendInfo(f"Active toolchain is {toolchain}")
        compileFunction = None

        if toolchain == ReservedValues.Configuration.Root.Toolchain.CLANG:
            self.errorIndicator = None
            self.warningIndicator = None
            compileFunction = self.__CompileWithClang
        elif toolchain == ReservedValues.Configuration.Root.Toolchain.GCC:
            self.errorIndicator = None
            self.warningIndicator = None
            compileFunction = self.__CompileWithGCC
        elif toolchain == ReservedValues.Configuration.Root.Toolchain.MSVC:
            self.errorIndicator = "error"
            self.warningIndicator = "warning"
            compileFunction = self.__CompileWithMSVC

        while self.config.LoadNextBuildStep() == ResultCode.SUCCESS and self.lastResultCode == ResultCode.SUCCESS:
            self.output.SendInfo(f"Starting build step '{self.config.GetBuildStepName()}'")
            self.lastResultCode = compileFunction()

        return self.lastResultCode

    def __CompileWithClang(self):
        compileCommand = ["clang"]
        return ResultCode.ERR_NOT_IMPLEMENTED

    def __CompileWithGCC(self):
        compileCommand = ["gcc"]
        return ResultCode.ERR_NOT_IMPLEMENTED

    def __CompileWithMSVC(self):
        compileCommand = ["cl", "/nologo"]

        # Append defines
        self.lastResultCode, defines = self.config.GetBuildStepDefines()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return self.lastResultCode

        for name, value in defines.items():
            defineArg = name
            if value is not None:
                if type(value) is str:
                    defineArg += f"=\"{value}\""
                else:
                    defineArg += f"={value}"

            compileCommand.append(f"/D{defineArg}")

        # Append target type
        self.lastResultCode, targetType = self.config.GetBuildStepTargetType()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return self.lastResultCode

        if targetType == ReservedValues.Configuration.Build.Target.Type.LIBRARY:
            compileCommand.append("/LD")

        # Append output paths
        self.lastResultCode, targetName = self.config.GetBuildStepTargetName()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return self.lastResultCode

        # pathlib strips trailing slash, but is needed for cl. Adding it back with os.path.join().
        targetPath = self.config.GetTargetOutputDir(PathType.RELATIVE) / self.buildName
        targetPath = os.path.join(targetPath, targetName)

        objDir = self.config.GetObjectOutputDir(PathType.RELATIVE) / self.buildName
        objDir = os.path.join(objDir, '')

        debugSymbolsDir = self.config.GetDebugSymbolsOutputDir(PathType.RELATIVE) / self.buildName
        debugSymbolsDir = os.path.join(debugSymbolsDir, '')

        compileCommand.append(f"/Fe:{targetPath}")
        compileCommand.append(f"/Fo:{objDir}")
        compileCommand.append(f"/Fd:{debugSymbolsDir}")

        # Append include directories
        self.lastResultCode, includeDirectories = self.config.GetBuildStepIncludeDirectories()
        if not self.lastResultCode in (ResultCode.SUCCESS, ResultCode.WRN_NO_VALUE):
            return self.lastResultCode

        if includeDirectories is not None:
            for dir in includeDirectories:
                with Path(dir) as includePath:
                    if not includePath.exists():
                        self.output.SendWarning(f"Skipping include directory '{includePath}' because it could not be found")
                        continue

                    compileCommand.append("/I")
                    compileCommand.append(str(includePath))

        # Append shared libraries
        self.lastResultCode, dynamicLibraries = self.config.GetBuildStepDynamicSharedLibraries()
        if not self.lastResultCode in (ResultCode.SUCCESS, ResultCode.WRN_NO_VALUE):
            return self.lastResultCode

        if dynamicLibraries is not None and len(dynamicLibraries) > 0:
            compileCommand.append("/MD")
            for lib in dynamicLibraries:
                compileCommand.append(lib)

        self.lastResultCode, staticLibraries = self.config.GetBuildStepStaticSharedLibraries()
        if not self.lastResultCode in (ResultCode.SUCCESS, ResultCode.WRN_NO_VALUE):
            return self.lastResultCode

        if staticLibraries is not None and len(staticLibraries) > 0:
            compileCommand.append("/MT")
            for lib in staticLibraries:
                compileCommand.append(lib)

        with self.config.GetObjectOutputDir(PathType.ABSOLUTE) / self.buildName as objFileRootPath:
            self.__ClearDirTree(objFileRootPath)

        self.lastResultCode, sourceExtension = self.config.GetBuildStepSourceExtension()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return self.lastResultCode

        self.lastResultCode, sourceDirectories = self.config.GetBuildStepSourceDirectories()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return self.lastResultCode

        # Append source file to compile command if modified time is more recent than object modified time
        for dir in sourceDirectories:
            with Path(dir) as sourcePath:
                if not sourcePath.exists() or not sourcePath.is_dir():
                    self.output.SendWarning(f"Skipping source directory '{sourcePath}' because it could not be found")
                    continue

                for item in sourcePath.iterdir():
                    if not item.is_file():
                        continue

                    fileName = item.parts[-1]
                    if not fileName.endswith(sourceExtension):
                        continue

                    compileCommand.append(str(item))

        # Append additional arguments
        self.lastResultCode, additionalArgs = self.config.GetBuildStepAdditionalArguments()
        if not self.lastResultCode in (ResultCode.SUCCESS, ResultCode.WRN_NO_VALUE):
            return self.lastResultCode

        if additionalArgs is not None:
            for arg in additionalArgs:
                compileCommand.append(arg)

        return self.__Execute(compileCommand)

    def __Execute(self, cmd: list[str]):
        executableName = cmd[0]

        self.output.SendInfoPrintOnly(f"Starting child process {executableName}")
        self.output.SendInfoLogOnly(f"Starting child process '{executableName}' with arguments {' '.join(cmd[1:])}")
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout:
            line = line.decode().strip()
            if not line == "":
                line = f"({executableName}) {line}"
                if self.errorIndicator in line:
                    self.output.SendError(line)
                elif self.warningIndicator in line:
                    self.output.SendWarning(line)
                else:
                    self.output.SendInfo(line)

        p.communicate()
        msg = f"Child process {executableName} exited with code {p.returncode}"
        if not p.returncode == 0:
            self.output.SendWarning(msg)
            return ResultCode.WRN_PROC_NONZERO_EXIT
        else:
            self.output.SendInfo(msg)
            return ResultCode.SUCCESS

    def __ClearDirTree(self, root: str):
        with Path(root) as treeRoot:
            if not treeRoot.exists():
                return

            for p in treeRoot.iterdir():
                if not p.is_dir():
                    os.remove(p)
                else:
                    self.__ClearDirTree(p)
                    os.rmdir(p)
