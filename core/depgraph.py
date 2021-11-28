'''
Copyright (C) 2021 Tayler Mauk and contributors. All rights reserved.
Licensed under the MIT license.
See LICENSE file in the project root for full license information.
'''

from pathlib import Path
import random
import sys

class DependencyGraphNode:
    def __init__(self, id: int, fileHash: str, filePath: Path):
        self.__id: int = id
        self.__childNodeIDs: list[int] = []
        self.fileHash: str = fileHash
        self.filePath: Path = filePath

    @property
    def id(self):
        return self.__id

    def GetChildren(self):
        return self.__childNodeIDs.copy()

    def HasChildren(self):
        return len(self.__childNodeIDs) != 0

    def HasChild(self, childID: int):
        return childID in self.__childNodeIDs

    def AddChild(self, childID: int):
        if not self.HasChild(childID):
            self.__childNodeIDs.append(childID)

    def RemoveChild(self, childID: int):
        if self.HasChild(childID):
            self.__childNodeIDs.remove(childID)

class DependencyGraph:
    def __init__(self):
        self.__nodes: dict[int, DependencyGraphNode] = {}

    def __getitem__(self, nodeID):
        return self.__nodes[nodeID]

    def __iter__(self):
        return iter(self.__nodes)

    def __len__(self):
        return len(self.__nodes)

    def SaveOrSerialize(self, filePath: Path):
        pass

    def Load(self, filePath: Path):
        pass

    def HasNode(self, nodeID: int):
        return nodeID in self.__nodes.keys()

    def AddNode(self, fileHash: str, filePath: Path):
        newNode = DependencyGraphNode(self.__GenerateNodeID(), fileHash, filePath)
        self.__nodes[newNode.id] = newNode
        return newNode.id

    def RemoveNode(self, nodeID: int):
        if self.HasNode(nodeID):
            self.__nodes.pop(nodeID)

        for node in self.__nodes.values():
            node.RemoveChild(nodeID)

    def AddChild(self, nodeID: int, fileHash: str, filePath: Path):
        if self.HasNode(nodeID):
            newNodeID = self.AddNode(fileHash, filePath)
            self.__nodes[nodeID].AddChild(newNodeID)

    def RemoveChild(self, nodeID: int, childID: int):
        if self.HasNode(nodeID):
            self.__nodes[nodeID].RemoveChild(childID)

    def __GenerateNodeID(self):
        newNodeID = -1
        isGenerated = False
        while not isGenerated and self.HasNode(newNodeID):
            newNodeID = random.randint(1, sys.maxsize)
            isGenerated = True

        return newNodeID
