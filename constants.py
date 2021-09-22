'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

class Configuration():
    class App():
        NAME    = "zbuild"
        VERSION = "2021.a"

        class Argsd():
            NAME = None

        class RootLocator():
            NAME = None

    class Files():
        DIR_NAME  = "config"
        EXTENSION = "json"

    class Root():
        FILE_NAME = None

    class Build():
        class Files():
            EXTENSION = None

    class Run():
        class Files():
            EXTENSION = None

Configuration.App.Argsd.NAME        = f"argsd.{Configuration.Files.EXTENSION}"
Configuration.App.RootLocator.NAME  = f"{Configuration.App.NAME}.root"
Configuration.Root.FILE_NAME        = f"root.{Configuration.Files.EXTENSION}"
Configuration.Build.Files.EXTENSION = f"b.{Configuration.Files.EXTENSION}"
Configuration.Run.Files.EXTENSION   = f"r.{Configuration.Files.EXTENSION}"

# Configuration key names as they should appear in json config files
class KeyNames():
    class Build():
        class SharedRecources():
            ROOT       = "shared"
            APPLIES_TO = "appliesTo"
            VALUE      = "value"

        class Steps():
            ROOT = "steps"

    class Root():
        class OutputDirectories():
            ROOT          = "outputDirectories"
            DEBUG_SYMBOLS = "debugSymbols"
            EXECUTABLE    = "executable"
            LOG           = "log"
            OBJECT        = "object"

        class Platform():
            ROOT = "platform"

        class Toolchain():
            ROOT = "toolchain"

# Reserved values that invoke a behavior instead of store a value
class ReservedValues():
    SHARED_RESOURCE_LOOKUP = "zbuild_lookup"

# Result codes returned from operations
class ResultCode():
    SUCCESS = 0x0

    ERR_NOT_IMPLEMENTED = 0x0100
    ERR_GENERIC         = 0x0101
    ERR_ARG_INVALID     = 0x0102
    ERR_DIR_NOT_FOUND   = 0x0103
    ERR_FILE_NOT_FOUND  = 0x0104
    ERR_KEY_NOT_FOUND   = 0x0105
    ERR_CONFIG_INVALID  = 0x0106
