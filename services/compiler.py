'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import os
from pathlib import Path
import subprocess

from services.configuration import ConfigurationService
from services.output import OutputService

class CompilerService:
    def __init__(self, config: ConfigurationService, output: OutputService):
        self.output = output
        self.config = config
        self.errorIndicator = None
        self.warningIndicator = None

    def __CompileWithClang(self):
        self.output.SendInfo("Active toolchain is clang")
        compileCommand = ["clang"]
        return False

    def __CompileWithGCC(self):
        self.output.SendInfo("Active toolchain is gcc")
        compileCommand = ["gcc"]
        return False

    def __CompileWithMSVC(self):
        self.output.SendInfo("Active toolchain is msvc")
        compileCommand = ["cl", "/nologo"]
        buildName = self.config.GetBuildName()

        # Append output directory paths
        # pathlib strips trailing slash, but is needed for cl. Adding it back with os.path.join().
        executablePath = self.config.GetExecutableOutputDir() / buildName
        executablePath = os.path.join(executablePath, self.config.ReadBuildKey("executableName"))

        objDir = self.config.GetObjectOutputDir() / buildName
        objDir = os.path.join(objDir, '')

        debugSymbolsDir = self.config.GetObjectOutputDir() / buildName
        debugSymbolsDir = os.path.join(debugSymbolsDir, '')

        compileCommand.append(f"/Fe:{executablePath}")
        compileCommand.append(f"/Fo:{objDir}")
        compileCommand.append(f"/Fd:{debugSymbolsDir}")

        # Append include directories
        for dir in self.config.ReadBuildKey("includeDirectories"):
            with Path(dir) as includePath:
                if not includePath.exists():
                    self.output.SendWarning(f"Could not find include path {includePath}")
                    continue

                compileCommand.append("/I")
                compileCommand.append(str(includePath))

        objModifiedTimes = {}
        objFilePaths = {}
        objFilesToRemove = []
        
        # Enumerate modification times of object files
        with self.config.GetObjectOutputDir() as objFileRootPath:
            if not objFileRootPath.exists():
                self.output.SendError(f"Could not find include path {objFileRootPath}")
                return

            for objFile in os.listdir(objFileRootPath.resolve()):
                if not objFile.endswith("obj"):
                    continue

                with Path(objFileRootPath / objFile) as objFilePath:
                    objModifiedTimes[objFilePath.stem] = objFilePath.lstat().st_mtime
                    objFilePaths[objFilePath.stem] = objFilePath.resolve()

        # Append source file to compile command if modified time is more recent than object modified time
        # FIXME: Look out, currently no files can have the same name! (Even in different dir)
        # TODO: Use glob wildcard if all source files in directory are being compiled?
        sourceExtension = self.config.ReadBuildKey("sourceExtension")
        for dir in self.config.ReadBuildKey("sourceDirectories"):
            with Path(dir) as sourcePath:
                if not sourcePath.exists():
                    self.output.SendWarning(f"Could not find source path {sourcePath}")
                    continue

                for sourceFile in os.listdir(sourcePath.resolve()):
                    if not sourceFile.endswith(sourceExtension):
                        continue

                    filePath = None
                    with Path(sourcePath / sourceFile) as sourceFilePath:
                        if sourceFilePath.stem in objModifiedTimes:
                            if objModifiedTimes[sourceFilePath.stem] > sourceFilePath.lstat().st_mtime:
                                filePath = objFilePaths[sourceFilePath.stem]
                            else:
                                objFilesToRemove.append(objFilePaths[sourceFilePath.stem])
                                filePath = str(sourcePath / sourceFile)
                        else:
                            filePath = str(sourcePath / sourceFile)
                        
                    compileCommand.append(filePath)

        # for f in objFilesToRemove:
        #     os.remove(f)
        
    ##### DEBUG
        print(compileCommand)
        print(f"OBJ to remove: {objFilesToRemove}")
        print(f"OBJ file paths: {objFilePaths}")
        compileCommand = ['cl', '/nologo', 'aaa']
    ####~ DEBUG

        self.__Execute(compileCommand)
        return

    def Compile(self):
        result = False
        toolchain = self.config.GetToolchain()

        dir = self.config.GetExecutableOutputDir() / self.config.GetBuildName()
        if dir.exists():
            self.__ClearDirTree(dir)
        else:
            os.makedirs(dir)

        # TODO: Add logic to handle multiple build steps

        if toolchain == "clang":
            self.errorIndicator = None
            self.warningIndicator = None
            result = self.CompileWithClang()
        elif toolchain == "gcc":
            self.errorIndicator = None
            self.warningIndicator = None
            result = self.CompileWithGCC()
        elif toolchain == "msvc":
            self.errorIndicator = "error"
            self.warningIndicator = "warning"
            result = self.CompileWithMSVC()

        return result

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

    def __ClearDirTree(self, root: str):
        for p in Path(root).iterdir():
            if not p.is_dir():
                os.remove(p)
            else:
                self.__ClearDirTree(p)
                os.rmdir(p)
