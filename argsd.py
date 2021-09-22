'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

import sys
from pathlib import Path
from typing import Any, Callable, Optional

from constants import ResultCode

class ArgHelper():
    def __init__(self, shortNameIndicator: str = "-", longNameIndicator: str = "--"):
        self.appName = Path(sys.argv[0]).parts[-1]
        self.helpMessageAddendums = []
        self.helpFormatter = _ArgHelpFormatter()
        self.shortNameIndicator = shortNameIndicator
        self.longNameIndicator = longNameIndicator

        self.helpArgDescriptor = _ArgDescriptor(
            shortName = f"{self.shortNameIndicator}h",
            longName = f"{self.longNameIndicator}help",
            helpInfo = "display this help message and exit",
            group = None,
            isSwitch = True
        )

        self.descriptors = [
            self.helpArgDescriptor
        ]

    def AddArg(self, shortName: str, longName: str, helpInfo: str,isSwitch: bool = False, isMulti: bool = False, group: Optional[int] = None, varName: Optional[str] = None, action: Optional[Callable] = None):
        if shortName is not None:
            shortName = f"{self.shortNameIndicator}{shortName}"
        longName = f"{self.longNameIndicator}{longName}"
        argd = _ArgDescriptor(shortName, longName, helpInfo, isSwitch, isMulti, group, varName, action)
        self.descriptors.append(argd)

    def AppendToHelpMessage(self, msg: str):
        self.helpMessageAddendums.append(msg)

    def ShowHelp(self):
        helpMsg = '\n'
        helpMsg += self.helpFormatter.GetUsageMessage(self.appName, self.descriptors)
        helpMsg += "\n\n"
        helpMsg += self.helpFormatter.GetArgumentsMessage(self.descriptors)
        helpMsg += '\n\n'

        for msg in self.helpMessageAddendums:
            helpMsg += f"{msg}\n"

        print(helpMsg.rstrip())

    def ShowInvalidUsageMessage(self, msg: str):
        print(f"{msg}\nUse {self.helpArgDescriptor.shortName} for help")

    def ParseArgs(self):
        # Remove invoked script name from args
        args = sys.argv[1:]

        if len(args) == 0 or self.helpArgDescriptor.shortName in args or self.helpArgDescriptor.longName in args:
            self.ShowHelp()
            exit()

        descriptorNamesSet = set()
        for argd in self.descriptors:
            descriptorNamesSet.add(argd.shortName)
            descriptorNamesSet.add(argd.longName)

        # Check for invalid arguments
        requestedArgGroups = []
        for arg in args:
            if arg.startswith(self.shortNameIndicator) or arg.startswith(self.longNameIndicator):
                if arg not in descriptorNamesSet:
                    self.ShowInvalidUsageMessage(f"Argument '{arg}' is not recognized")
                    return (ResultCode.ERR_ARG_INVALID, None)
                else:
                    for argd in self.descriptors:
                        if arg in (argd.shortName, argd.longName):
                            if argd.group not in requestedArgGroups:
                                requestedArgGroups.append(argd.group)
                            else:
                                groupMsg = "You can only specify one of the following:\n    "
                                for a in self.descriptors:
                                    if a.group == argd.group:
                                        groupMsg += f"{a.shortName if a.shortName is not None else a.longName} | "
                                groupMsg = groupMsg.rstrip(" | ")
                                self.ShowInvalidUsageMessage(groupMsg)
                                return (ResultCode.ERR_ARG_INVALID, None)

        # Arguments should be valid at this point, process arguments
        actions: list[tuple[Callable, Any]] = []
        i = 0
        while i < len(args):
            arg = args[i]

            for argd in self.descriptors:
                if arg in (argd.shortName, argd.longName):
                    if argd.isSwitch:
                        actions.insert(0, (argd.action, None))
                    elif argd.isMulti:
                        i += 1
                        argValueList = []
                        while i < len(args) and args[i] not in descriptorNamesSet:
                            argValueList.append(args[i])
                            i += 1
                        actions.append((argd.action, argValueList))
                    else:
                        i += 1
                        actions.append((argd.action, args[i]))
                        
                    break

            i += 1

        if len(actions) == 0:
            self.ShowInvalidUsageMessage("Values with no arguments provided")
            return (ResultCode.ERR_ARG_INVALID, None)
        return (ResultCode.SUCCESS, actions)

class _ArgDescriptor():
    def __init__(self, shortName: str, longName: str, helpInfo: str,isSwitch: bool = False, isMulti: bool = False, group: Optional[int] = None, varName: Optional[str] = None, action: Optional[Callable] = None):
        self.shortName = shortName
        self.longName = longName
        self.helpInfo = helpInfo
        self.isSwitch = isSwitch
        self.isMulti = isMulti
        self.group = group
        self.varName = longName if varName is None else varName
        self.action = action

        self.varName = self.__SanitizeVariableName(self.varName)

    def __SanitizeVariableName(self, varName: str):
        nameStartIndex = 0
        for i in range(len(varName)):
            currentChar = varName[i]
            if currentChar.isalnum():
                nameStartIndex = i
                break

        return varName[nameStartIndex:].replace('-', '_')

class _ArgHelpFormatter():
    def __init__(self):
        self.MAX_LINE_LENGTH = 80

    def GetUsageMessage(self, appName:str,  argDescriptors: list[_ArgDescriptor]):
        argGroups: list[list[_ArgDescriptor]] = []
        groupedArgDescriptors = []
        for a in argDescriptors:
            if a in groupedArgDescriptors:
                continue

            argGroup = []
            argGroup.append(a)
            groupedArgDescriptors.append(a)
            if a.group is not None:
                for b in argDescriptors:
                    if not a == b and a.group == b.group:
                        argGroup.append(b)
                        groupedArgDescriptors.append(b)

            argGroups.append(argGroup)

        usageMsgTokens = [f"    {appName} "]
        usageMsg = ""
        for argGroup in argGroups:
            usageMsg += '['

            argGroupLength = len(argGroup)
            for i in range(argGroupLength):
                arg = argGroup[i]
                if arg.shortName is not None:
                    usageMsg += f"{arg.shortName}"
                else:
                    usageMsg += f"{arg.longName}"

                if not arg.isSwitch:
                    usageMsg += f" <{arg.varName}>"

                if not i + 1 == argGroupLength:
                    usageMsg += " | "
                    usageMsgTokens.append(usageMsg)
                    usageMsg = ""

            usageMsg += "] "
            usageMsgTokens.append(usageMsg)
            usageMsg = ""

        usageLeftPadLength = len(usageMsgTokens[0])
        usageMsg = ""
        lineLength = 0
        for t in usageMsgTokens:
            tokenLength = len(t)
            if lineLength + tokenLength > self.MAX_LINE_LENGTH:
                usageMsg += '\n' + (' ' * usageLeftPadLength)
                lineLength = usageLeftPadLength

            usageMsg += t
            lineLength += tokenLength

        return f"Usage:\n{usageMsg}"

    def GetArgumentsMessage(self, argDescriptors: list[_ArgDescriptor]):
        # Get longest long name so help info is left justified
        longestLongNameLength = 0
        for a in argDescriptors:
            nameLength = len(a.longName)
            if nameLength > longestLongNameLength:
                longestLongNameLength = nameLength

        # Get longest short name so args with long names are left justified
        longestShortNameLength = 0
        for a in argDescriptors:
            if a.shortName is not None:
                nameLength = len(a.shortName)
                if nameLength > longestShortNameLength:
                    longestShortNameLength = nameLength

        helpInfoLeftPadLength = (longestShortNameLength + 2 + 4) + (longestLongNameLength + 4)
        argsMsgLines = []
        for a in argDescriptors:
            midSpacer = ' ' * (longestLongNameLength - len(a.longName) + 4)
            msgLine = ""

            if a.shortName is not None:
                lnSpacer = ' ' * (longestShortNameLength - len(a.shortName) + 1)
                msgLine = (' ' * 4) + f"{a.shortName},{lnSpacer}"
            else:
                msgLine = ' ' * (longestShortNameLength + 2 + 4)
            
            msgLine += f"{a.longName}{midSpacer}"

            for word in a.helpInfo.split():
                if len(msgLine) + len(word) > self.MAX_LINE_LENGTH:
                    argsMsgLines.append(msgLine)
                    msgLine = ' ' * helpInfoLeftPadLength
                
                msgLine += f"{word} "

            argsMsgLines.append(msgLine)

        argsMsg = ""
        for line in argsMsgLines:
            argsMsg += f"{line}\n"

        return f"Arguments:\n{argsMsg}".rstrip()
