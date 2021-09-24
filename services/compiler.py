'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import os
from pathlib import Path
import subprocess

from constants import ReservedValues, ResultCode
from services.configuration import ConfigurationService
from services.output import OutputService

class CompilerService:
    def __init__(self, config: ConfigurationService, output: OutputService):
        self.output = output
        self.config = config
        self.errorIndicator = None
        self.warningIndicator = None
        self.lastResultCode = ResultCode.SUCCESS

    def Compile(self):
        resultCode = ResultCode.SUCCESS
        toolchain = self.config.GetToolchain()

        dir = self.config.GetTargetOutputDir() / self.config.GetBuildName()
        if dir.exists():
            self.__ClearDirTree(dir)
        else:
            os.makedirs(dir)

        # TODO: Add logic to handle multiple build steps
        self.config.LoadNextBuildStep()

        if toolchain == "clang":
            self.errorIndicator = None
            self.warningIndicator = None
            resultCode = self.__CompileWithClang()
        elif toolchain == "gcc":
            self.errorIndicator = None
            self.warningIndicator = None
            resultCode = self.__CompileWithGCC()
        elif toolchain == "msvc":
            self.errorIndicator = "error"
            self.warningIndicator = "warning"
            resultCode = self.__CompileWithMSVC()

        return resultCode

    def __CompileWithClang(self):
        self.output.SendInfo("Active toolchain is clang")
        compileCommand = ["clang"]
        return ResultCode.ERR_NOT_IMPLEMENTED

    def __CompileWithGCC(self):
        self.output.SendInfo("Active toolchain is gcc")
        compileCommand = ["gcc"]
        return ResultCode.ERR_NOT_IMPLEMENTED

    def __CompileWithMSVC(self):
        self.output.SendInfo("Active toolchain is msvc")
        compileCommand = ["cl", "/nologo"]
        buildName = self.config.GetBuildName()

        # Append defines
        self.lastResultCode, defines = self.config.GetBuildStepDefines()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        for name, value in defines.items():
            defineArg = name
            if value is not None:
                defineArg += f"={value}"
            
            compileCommand.append(f"/D\"{defineArg}\"")

        # Append target type
        self.lastResultCode, targetType = self.config.GetBuildStepTargetType()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        if targetType == ReservedValues.Configuration.Build.Target.Type.LIBRARY:
            compileCommand.append("/LD")

        self.lastResultCode, targetName = self.config.GetBuildStepTargetName()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        # Append output paths
        # pathlib strips trailing slash, but is needed for cl. Adding it back with os.path.join().
        targetPath = self.config.GetTargetOutputDir() / buildName
        targetPath = os.path.join(targetPath, targetName)

        objDir = self.config.GetObjectOutputDir() / buildName
        objDir = os.path.join(objDir, '')

        debugSymbolsDir = self.config.GetDebugSymbolsOutputDir() / buildName
        debugSymbolsDir = os.path.join(debugSymbolsDir, '')

        compileCommand.append(f"/Fe:{targetPath}")
        compileCommand.append(f"/Fo:{objDir}")
        compileCommand.append(f"/Fd:{debugSymbolsDir}")

        # Append include directories
        self.lastResultCode, includeDirectories = self.config.GetBuildStepIncludeDirectories()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        for dir in includeDirectories:
            with Path(dir) as includePath:
                if not includePath.exists():
                    self.output.SendWarning(f"Skipping include directory '{includePath}' because it could not be found")
                    continue

                compileCommand.append("/I")
                compileCommand.append(str(includePath))

        # Append shared libraries
        self.lastResultCode, dynamicLibraries = self.config.GetBuildStepDynamicSharedLibraries()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        for lib in dynamicLibraries:
            compileCommand.append("/MD")
            compileCommand.append(lib)

        self.lastResultCode, staticLibraries = self.config.GetBuildStepStaticSharedLibraries()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        for lib in staticLibraries:
            compileCommand.append("/MT")
            compileCommand.append(lib)

        objModifiedTimes = {}
        objFilePaths = {}
        objFilesToRemove = []
        
        # Enumerate modification times of object files
        with self.config.GetObjectOutputDir() as objFileRootPath:
            if not objFileRootPath.exists():
                self.output.SendWarning(f"Skipping object directory '{objFileRootPath}' because it could not be found")
            else:
                for objFile in os.listdir(objFileRootPath.resolve()):
                    if not objFile.endswith("obj"):
                        continue

                    with Path(objFileRootPath / objFile) as objFilePath:
                        objFileName = objFilePath.parts[-1]
                        objModifiedTimes[objFileName] = objFilePath.lstat().st_mtime
                        objFilePaths[objFileName] = objFilePath.resolve()

        self.lastResultCode, sourceExtension = self.config.GetBuildStepSourceExtension()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        self.lastResultCode, sourceDirectories = self.config.GetBuildStepSourceDirectories()
        if not self.lastResultCode == ResultCode.SUCCESS:
            return ResultCode.ERR_GENERIC

        # FIXME: Look out, currently no files can have the same name! (Even in different dir)
        # TODO: Use glob wildcard if all source files in directory are being compiled?

        # Append source file to compile command if modified time is more recent than object modified time
        for dir in sourceDirectories:
            with Path(dir) as sourcePath:
                if not sourcePath.exists():
                    self.output.SendWarning(f"Skipping source directory '{sourcePath}' because it could not be found")
                    continue

                for sourceFile in os.listdir(sourcePath.resolve()):
                    if not sourceFile.endswith(sourceExtension):
                        continue

                    filePath = None
                    with Path(sourcePath / sourceFile) as sourceFilePath:
                        fileName = sourceFilePath.parts[-1]
                        if fileName in objModifiedTimes:
                            if objModifiedTimes[fileName] > sourceFilePath.lstat().st_mtime:
                                filePath = objFilePaths[fileName]
                            else:
                                objFilesToRemove.append(objFilePaths[fileName])
                                filePath = str(sourceFilePath)
                        else:
                            filePath = str(sourceFilePath)

                    compileCommand.append(filePath)

        for f in objFilesToRemove:
            os.remove(f)

    ##### DEBUG
        print(compileCommand)
        return ResultCode.SUCCESS
    ###~ DEBUG

        return self.__Execute(compileCommand)

    def __Execute(self, cmd: str):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout:
            line = line.decode().strip()
            if not line == "":
                if self.errorIndicator in line:
                    self.output.SendError(line)
                elif self.warningIndicator in line:
                    self.output.SendWarning(line)
                else:
                    self.output.SendInfo(line)

        p.communicate()
        msg = f"Compilation process exited with code {p.returncode}"
        if not p.returncode == 0:
            self.output.SendWarning(msg)
            return ResultCode.WRN_PROC_NONZERO_EXIT
        else:
            self.output.SendInfo(msg)
            return ResultCode.SUCCESS

    def __ClearDirTree(self, root: str):
        for p in Path(root).iterdir():
            if not p.is_dir():
                os.remove(p)
            else:
                self.__ClearDirTree(p)
                os.rmdir(p)
