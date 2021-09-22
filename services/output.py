'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

from datetime import datetime
from enum import Enum
import os
from pathlib import Path

class MessageType(Enum):
    ERROR   = 0
    INFO    = 1
    WARNING = 2

class OutputService:
    def __init__(self, logPath: str):
        with Path(logPath) as logFilePath:
            logDirpath = logFilePath.parent
            if not logDirpath.exists():
                os.makedirs(logDirpath)
        
            self.logFile = open(logFilePath, "a")

    def Close(self):
        self.logFile.close()

    def SendError(self, msg: str):
        self.__Send(MessageType.ERROR, msg)

    def SendInfo(self, msg: str):
        self.__Send(MessageType.INFO, msg)

    def SendWarning(self, msg: str):
        self.__Send(MessageType.WARNING, msg)

    def SendErrorPrintOnly(self, msg: str):
        self.__SendPrintOnly(self.__FormatMessage(MessageType.ERROR, msg))

    def SendInfoPrintOnly(self, msg: str):
        self.__SendPrintOnly(self.__FormatMessage(MessageType.INFO, msg))

    def SendWarningPrintOnly(self, msg: str):
        self.__SendPrintOnly(self.__FormatMessage(MessageType.WARNING, msg))

    def SendErrorLogOnly(self, msg: str):
        self.__SendLogOnly(self.__FormatMessage(MessageType.ERROR, msg))

    def SendInfoLogOnly(self, msg: str):
        self.__SendLogOnly(self.__FormatMessage(MessageType.INFO, msg))

    def SendWarningLogOnly(self, msg: str):
        self.__SendLogOnly(self.__FormatMessage(MessageType.WARNING, msg))

    def __FormatMessage(self, msgType: MessageType, msg: str):
        msgIcon = None
        if msgType == MessageType.ERROR:
            msgIcon = '!'
        elif msgType == MessageType.WARNING:
            msgIcon = '#'
        else:
            msgIcon = ' '

        return f"[ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ][ {msgIcon} ] {msg}"

    def __SendLogOnly(self, msg: str):
        self.logFile.write(f"{msg}\n")
        self.logFile.flush()

    def __SendPrintOnly(self, msg: str):
        print(msg)

    def __Send(self, msgType: str, msg: str):
        msgComplete = self.__FormatMessage(msgType, msg)
        self.__SendPrintOnly(msgComplete)
        self.__SendLogOnly(msgComplete)
