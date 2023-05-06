
#!/usr/bin/env python3
from lib.ParseFile import ParseTXTConfig
import unittest
import json
import sys
from typing import List, Dict
from copy import deepcopy
from abc import ABC,abstractmethod
from lib.nvdsanalystic_config_model import ROIConfig, OverCrowdingConfig, LineCrossConfig, DirectionConfig, PropertyConfig
from typing import Union

sys.path.append('../')


class AnalyticItem(object):
    def __init__(self,itemType: str, name: str, availableClasses: list, **kwargs):
        self.type = itemType
        self.name = name
        self.totalCount = 0
        self.parseCount = {}
        for class_ in availableClasses:
            self.parseCount.update({class_ : 0})
        #self.parseCountCopy = self.parseCount
    def Total_parse_count(self):
        #print("total val: {}".format(self.totalCount))
        total = 0
        for className, value in self.parseCount.items():
            total = total + value
        return total

    def GetCountOfClass(self, className: str):
         return self.parseCount[className]
    
    def IncreaseCountOfClass(self, className):
        self.parseCount[className] += 1


    def UpdateCountOfClass(self,className ,countVal):
        self.parseCount[className] = countVal

    def ResetAllCount(self):
        for key, val in self.parseCount.items():
            self.parseCount[key] = 0


    
        
class ConvertObject2Dict(ABC):
    @abstractmethod
    def convertData(self, object: AnalyticItem) -> dict:
        pass

class BasicAnalyticItem2Dict(ConvertObject2Dict):
    def convertData(self, object: AnalyticItem) -> dict:
        dictData = {"total": object.totalCount}
        return dictData

class FullAnalyticItem2Dict(ConvertObject2Dict):
    def convertData(self, object: AnalyticItem) -> dict:

        if object.type == "ROI":
            if object.totalCount == object.Total_parse_count():
                dictData = {"total": object.totalCount, "parse": object.parseCount}
                return dictData
            else:
                return None
        else:
            dictData = {"total": object.totalCount, "parse": object.parseCount}
            return dictData


class ParseAnalyticItem2Dict(ConvertObject2Dict):
    def convertData(self, object: AnalyticItem) -> dict:
        dictData = {"parse": object.parseCount}
        return dictData

class TargetAnalyticItem2Dict(ConvertObject2Dict):
    def convertData(self, object: AnalyticItem, targetLabel: str) -> dict:
        dictData = {"total": object.totalCount}
        parseData = {}
        if targetLabel in list(object.parseCount.keys()):
            parseData.update(targetLabel, object.parseCount[targetLabel])
            dictData.update("parse", parseData)

        return dictData
        
class CameraAnalystic():
    def __init__(self, ID):
        self.ID = ID
        self.listROI : Dict[str, AnalyticItem] = {}
        self.listLineCross: Dict[str, AnalyticItem] = {}
        self.listOverCrowding: Dict[str, AnalyticItem] = {}
        self.listDirection: Dict[str, AnalyticItem] = {}

    

    def UpdateROITotalCount(self, ROIName, newCount):
        try:
            updateItem = self.listROI[ROIName]
            updateItem.totalCount = newCount
            
        except:
            raise ValueError("Cannot find %s ,%s" % (ROIName,self.ID))
        

    def UpdateLineCrossCount(self, lineCrossName, newCount):
        try:
            updateItem = self.listLineCross[lineCrossName]
            updateItem.totalCount = newCount
        except:
            raise ValueError("Cannot find %s" % lineCrossName)

    def UpdateOverCrowding(self, overCrowdingName, newCount):
        try:
            updateItem = self.listOverCrowding[overCrowdingName]
            updateItem.totalCount = newCount
        except:
            raise ValueError("Cannot find %s" % overCrowdingName)  

    def UpdateDirection(self, directionName, newCount):
        try:
            updateItem = self.listOverCrowding[directionName]
            updateItem.totalCount = newCount
        except:
            raise ValueError("Cannot find %s" % directionName)


    def AddROI(self,name:str, roi: AnalyticItem):
        self.listROI.update({name: roi})

    def AddLineCross(self,name, lineCross: AnalyticItem):
        self.listLineCross.update({name: lineCross})
    
    def AddOverCrowding(self, name, overCrowding: AnalyticItem):
        self.listOverCrowding.update({name: overCrowding})

    def AddDirection(self, name, direction: AnalyticItem):
        self.listDirection.update({name: direction})


    def _ConvertROI2Dict(self, convertMethod: ConvertObject2Dict):
        data :Dict[str, int] ={}
        for key,roi in self.listROI.items():
            value = convertMethod.convertData(object = roi)
            if value != None:
            #print(roi.ConvertData2Dict())
                data.update({key: convertMethod.convertData(object = roi)})
                
            else:
            
                return None
        return data

    def _ConvertLineCross2Dict(self, convertMethod: ConvertObject2Dict):
        data  :Dict[str, int] ={}
        for key,lineCross in self.listLineCross.items():
            value = convertMethod.convertData(object = lineCross)
            if value != None:
            #print(roi.ConvertData2Dict())
                data.update({key: value})
                
            else:
          
                return 
        return data

    def _ConvertDirection2Dict(self, convertMethod :ConvertObject2Dict):
        data  :Dict[str, int] ={}
        for key, direction in self.listDirection.items():
            value = convertMethod.convertData(object = direction)
            if value != None:
            #print(roi.ConvertData2Dict())
                data.update({key: value})
                
            else:
 
                return None
        return data
            
    def _ConvertOverCrowd2Dict(self, convertMethod: ConvertObject2Dict):
        data  :Dict[str, int] ={}
        for key, overCrowd in self.listOverCrowding.items():
            value = convertMethod.convertData(object = overCrowd)
            if value != None:
                
            #print(roi.ConvertData2Dict())
                data.update({key: value})
            else:
                return None
        return data
    
    def ConvertData_of_camera_to_dict(self, convertMethod: ConvertObject2Dict):
        ROIData = self._ConvertROI2Dict(convertMethod)
        if ROIData == None:
            #raise ValueError("No ROIData")
            return None
        lineData = self._ConvertLineCross2Dict(convertMethod)
        if lineData == None:
            #raise ValueError("No line Data")
            return None
        overCrowdData = self._ConvertOverCrowd2Dict(convertMethod)
        if overCrowdData == None:
            #raise ValueError("No overcrowd Data")
            return None
        directionData = self._ConvertDirection2Dict(convertMethod)
        if directionData == None:
            #raise ValueError("No direction Data")
            return None
        
        data = {"R": ROIData, "C": overCrowdData, "L": lineData, "D": directionData}
        return data


    def GetAllROIName(self):
        return self.listROI.keys()

    def GetAllLineCrossName(self):
        return self.listLineCross.keys()

    def GetAllOverCrowdName(self):
        return self.listOverCrowding.keys()

    



class TransmitFrameConfig(object):
    def __init__(self, analysticFile, labelFile):
        self.parse = ParseTXTConfig(analysticFile)
        self.allCameraAnalystic : Dict[str, CameraAnalystic] = {}
        self.allAnalyticItems : Dict[str, AnalyticItem] = {}
        allData = self.parse.ReadData()
        self.allClasses = self._GetLabelsFromFile(labelFile)
       
        _availableID = []
        self.serverID = int(allData['optionConfig']['server_id'])
        
        for key,val in allData.items():
            if len(key.split("-")) > 1:
                streamID = int(key.split("-")[-1])
                itemType = key.split("-")[0]
                if streamID not in _availableID:
                    newCameraAnalystic = CameraAnalystic(ID = streamID)
                    self.allCameraAnalystic.update({str(streamID) : newCameraAnalystic})
                    _availableID.append(streamID)
                    
                if itemType == "roi":
                    roiConfig = ROIConfig(streamID = streamID)
                    roiConfig.UpdatePropertyFromDict(key, val)
                    listROI = roiConfig.GetAllROIName()
                    allClass = roiConfig.availableClass
                    for roiName in listROI:
                        newItem = AnalyticItem(itemType = "ROI", name = roiName, availableClasses = self._Convert2ClassesName(allClass))
                        self.allCameraAnalystic[str(streamID)].AddROI(roiName, newItem)
                        self.allAnalyticItems.update({roiName: newItem})


                elif itemType == "direction":
            
                    directConfig = DirectionConfig(streamID = streamID)
                    directConfig.UpdatePropertyFromDict(key,val)
                    listDirection = directConfig.GetAllDirectionName()
                    allClass = directConfig.availableClass
                    for directName in listDirection:
                        newItem = AnalyticItem(itemType = "direction", name = directName, availableClasses= self._Convert2ClassesName(allClass))
                        self.allCameraAnalystic[str(streamID)].AddDirection(directName, newItem)
                        self.allAnalyticItems.update({directName: newItem})
                    #print("all roi: ".format(newCameraAnalystic.listDirection))
                    
                elif itemType == "line":
                    lineCrossConfig = LineCrossConfig(streamID = streamID)
                    #print(val)
                    lineCrossConfig.UpdatePropertyFromDict(key,val)
                    listLineCross = lineCrossConfig.GetAllLineName()
                    #print("all name: ".format(listLineCross))
                    allClass = lineCrossConfig.availableClass
                    for lineCrossName in listLineCross:
                        newItem = AnalyticItem(itemType = "line", name = lineCrossName, availableClasses = self._Convert2ClassesName(allClass))
                        self.allCameraAnalystic[str(streamID)].AddLineCross(lineCrossName, newItem)
                        self.allAnalyticItems.update({lineCrossName: newItem})
                        
                        
                
                elif itemType == "overcrowding":
                    overCrowdConfig = OverCrowdingConfig(streamID = streamID)
                    overCrowdConfig.UpdatePropertyFromDict(key,val)
                    listOverCrowd = overCrowdConfig.GetAllROIName()
                    allClass = overCrowdConfig.availableClass
                    for overCrowdName in listOverCrowd:
                        newItem = AnalyticItem(itemType = "overcrowding", name = overCrowdName, availableClasses = self._Convert2ClassesName(allClass))
                        self.allCameraAnalystic[str(streamID)].AddOverCrowding(overCrowdName, newItem)
                        self.allAnalyticItems.update({overCrowdName: newItem})

    
        
    def GetIDFromItemName(self, itemName: str, type: str, **kwargs) -> int:
        itemIndex = 0
        for cameraID, camera in self.allCameraAnalystic.items():
            if type == "roi":
                if itemName in camera.GetAllROIName():
                    itemIndex = int(cameraID)# cameraID is str so it must be convert to int
                    break
        return itemIndex
        
    #Convert class index to class Name 
    def _Convert2ClassesName(self, listIndex):
        listClasses = []
        for index in listIndex:
            if index == -1:
                listClasses = self.allClasses

            else:
                listClasses.append(self.allClasses[index])

        return listClasses

    def _GetLabelsFromFile(self, labelFile):
        with open(labelFile, 'r') as file:
            allLabels = file.read().split('\n')[:-1]
            print("all labels value: {}".format(allLabels))
        return allLabels
        
    def UpdateItemTotalCount(self, cameraID, type, itemName, newValue, **kwargs):
        cameraAnalystic = self.allCameraAnalystic[str(cameraID)]
        if type == "roi":
            cameraAnalystic.UpdateROITotalCount(itemName, newValue)

        elif type == "line":
            cameraAnalystic.UpdateLineCrossCount(itemName, newValue)
        
        elif type == "overcrowding":
            cameraAnalystic.UpdateOverCrowding(itemName, newValue)

    def Convert2JSONFormat(self, convertMethod: ConvertObject2Dict):
        data = {}
        for cameraID,camera in self.allCameraAnalystic.items():
            camData = camera.ConvertData_of_camera_to_dict(convertMethod)
            if camData == None:
                return None
            else:
                data.update({cameraID: camData})
        return data
    
    def Convert2Message(self, convertMethod: ConvertObject2Dict):
        messageData = {}
        for analyticName, analyticData in self.allAnalyticItems.items():
            data = convertMethod.convertData(analyticData)
            if data != None:
                messageData.update({analyticName: data})
            else:
                return None
        return messageData


    def ResetAllData(self):
        for key, val in self.allAnalyticItems.items():
            self.allAnalyticItems[key].ResetAllCount()
        
    # def UpdateCountValue(self, cameraID, type, itemName , newValue, **kwargs):
    #     cameraAnalystic = self.listCameraAnalystic[cameraID]
    #     if type == 
     
if __name__ == "__main__":
   
    transmitFrame = TransmitFrameConfig("./config_file/analytic_config/config_forBox.txt", "./config_file/infer_config/label/labelV5.txt")
    print("runnin2")
    # transmitFrame.UpdateItemTotalCount(cameraID = 0, type = "roi", itemName = "robot_area", newValue = 10)
    # transmitFrame.UpdateItemTotalCount(cameraID = 1, type = "roi", itemName = "cua_vao", newValue = 10)
    # transmitFrame.allCameraAnalystic["0"].listROI["robot_area"].UpdateCountOfClass("box", 10)
    # transmitFrame.allCameraAnalystic["1"].listROI["cua_vao"].UpdateCountOfClass("box", 10)
    transmitFrame.allAnalyticItems["k1"].UpdateCountOfClass("cone", 10)
    transmitFrame.allAnalyticItems["k2"].UpdateCountOfClass("cone", 10)
    transmitFrame.allAnalyticItems["k1"].totalCount = 10
    transmitFrame.allAnalyticItems["k2"].totalCount = 10


    data = transmitFrame.Convert2Message(FullAnalyticItem2Dict())
    print(data)
    