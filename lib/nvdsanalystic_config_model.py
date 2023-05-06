import os
import glob
import sys
import glob
from collections import deque
import unittest
#from lib import Controller

LOOSE = "loose"
BALANCED = "balanced"
STRICT = "strict"
minX = 0
maxX = 1915
minY = 0
maxY = 1075
class ObjectConfig(object):
    def __init__(self,streamID = 0, streamName = "object_1", enable = True, **kwargs):
        self.availableClass = []
        self.streamID = streamID
        self.streamName = streamName
        self.enable = enable

    @property
    def SetStreamID(self):
        return self.streamID

    @SetStreamID.setter
    def SetStreamID(self, streamID):
        self.streamID = streamID
    
    @property
    def SetStreamName(self):
        return self.streamName

    @SetStreamName.setter

    def SetStreamName(self, streamName):
        self.streamName = streamName
    
    def AddClass(self, objectClass):
        """
        This function adds a class to the list of available classes
        
        :param objectClass: The class of the object you want to add
        """
        if objectClass not in self.availableClass:
            if objectClass == -1:
                self.availableClass.clear()
                self.availableClass.append(-1)
            else:
                if self.availableClass != []:
                    if objectClass != -1 and self.availableClass[0] == -1:
                        self.availableClass.clear()
                        self.availableClass.append(objectClass)
                    else:
                        self.availableClass.append(objectClass)
                else:
                    self.availableClass.append(objectClass)
               
            return True
        else:
            return False

    def RemoveClass(self, objectClass):
        if objectClass == -1:
            self.availableClass.clear()

        elif objectClass in self.availableClass:
            self.availableClass.remove(objectClass)
            return True 
        return False


class LineCross():
    def __init__(self, ID = 0, name = "line_1", startLine = (0,0), endLine = (0,0), startDirect = (0,0), endDirect = (0,0), avaiClass = [], **kwargs):
        self.ID = ID
        self.name = name
        self.startLine = startLine
        self.endLine = endLine
        self.startDirect = startDirect
        self.endDirect = endDirect
        self.avaiClass = avaiClass

    @property
    def SetName(self):
        return self.name
    
    @SetName.setter
    def SetName(self, name):
        if isinstance(name, str):
            self.name = name

    @property
    def SetStartLine(self):
        return self.startLine

    @SetStartLine.setter

    def SetStartLine(self, startPoint):
        
        if isinstance(startPoint[0], int) == True and isinstance(startPoint[1], int) == True:
            self.startLine = startPoint

        else:
            raise TypeError("Point value must be an interger")

    @property

    def SetEndLine(self):
        return self.endLine

    @SetEndLine.setter
    def SetEndLine(self, endPoint):

        if isinstance(endPoint[0], int) == True and isinstance(endPoint[1], int) == True:
            self.endLine = endPoint

        else:
            raise TypeError("Point value must be an integer")

    @property
    def SetStartDirect(self):
        return self.startDirect

    @SetStartDirect.setter
    def SetStartDirect(self, startPoint):
        if isinstance(startPoint[0], int) == True and isinstance(startPoint[1], int) == True:
            self.startDirect = startPoint

        else:
            raise TypeError("Point value must be an integer")

    @property

    def SetEndDirect(self):
        return self.endDirect

    @SetEndDirect.setter
    def SetEndDirect(self, endPoint):
     
        if isinstance(endPoint[0], int) == True and isinstance(endPoint[1], int) == True:
            self.endDirect = endPoint

        else:
            raise TypeError("Point value must be an integer")

    def __call__(self):
        print("Line: %s" % self.name)


class LineCrossConfig(ObjectConfig):

    def __init__(self, streamID = 0, streamName = "lin", mode = BALANCED, extended = False, enable = True):
        super(LineCrossConfig, self).__init__(streamID, streamName, enable)
        self.mode = mode
        self.extended = extended
        self.listLine = []
     
    @property
    def SetMode(self):
        return self.mode

    @SetMode.setter

    def SetMode(self, mode):
        self.mode = mode

    def GetLineCross(self, lineName):
        
        index = self.GetAllLineName().index(lineName)
        lineCross = self.listLine[index]
        return lineCross

    
    def GetAllLineName(self):
        listName = []

        for line in self.listLine:
            listName.append(line.name)
        return listName

    def GetAllLineID(self):
        listID = []
        
        for line in self.listLine:
            listID.append(line.ID)

        return listID

    def AddLine(self, lineCross: LineCross, **kwargs):
        """
        If the lineCross is a LineCross type and the ID is not in the list of all line IDs, then add the
        lineCross to the list of lines
        
        :param lineCross: LineCross
        :type lineCross: LineCross
        """

        if isinstance(lineCross, LineCross):

            if lineCross.ID not in self.GetAllLineID():
                self.listLine.append(lineCross)

            else:
                raise ValueError("Line cross with ID already exists")

        else:
            raise TypeError("Only except LineCross type")

    def RemoveLineWithName(self, name: str):
        """
        It removes a line from the list of lines in the class
        
        :param name: The name of the line to be deleted
        :type name: str
        """

        if isinstance(name, str):
            index = self.GetAllLineName().index(name)
            self.listLine.pop(index)

    def GetLineWithName(self, name):
        index = self.GetAllLineName().index(name)
        return self.listLine[index]


    def UpdateDirection(self, nameOfDirection :str, newLine: LineCross, **kwargs):
        """
        This function replace the current Direction with  a new Direction with the same name. It often used when the ROI has any change
        
        :nameOfDirection: Name of the Direction needed to be updated
        :newROI: the new ROI which is used to replace the current ROI
        """
        if isinstance(newLine, LineCross):
            line = self.GetLineWithName(nameOfDirection)
            line = newLine

    def UpdateLine(self,nameOfLine: str , newLine: LineCross):
        """
        This function replace the current LineCross with  a new LineCross with the same name. It often used when the ROI has any change
        
        :nameOfLine: Name of the Line needed to be updated
        :newLine: the new LineCross which is used to replace the current LineCross
        """
        if isinstance(newLine, LineCross):
            self.RemoveLineWithName(nameOfLine)
            self.AddLine(newLine)



    def RemoveLineWithID(self, ID: int):
        """
        It removes a line from the list of lines in the class
        
        :param ID: The ID of the line to be removed
        :type ID: int
        """
        if isinstance(ID, int):
            index = self.GetAllLineID().index(ID)
            self.listLine.pop(index)
        else:
            print("error")

    def RemoveAllLine(self):
        self.listLine.clear()

    def Property2DictFormat(self):
        classData = ""
        for index, classObject in enumerate(self.availableClass):
            
            if index == len(self.availableClass) - 1:
                classData += str(classObject)
            else:
                classData += (str(classObject) + ";")
        mode = "loose"
        if self.mode == LOOSE:
            mode = "loose"

        elif self.mode == BALANCED:
            mode = "balanced"

        elif self.mode == STRICT:
            mode = "strict"

        dictData = {"enable":str(1) if self.enable == True else str(0), "mode": mode, "extended":  str(1) if self.extended == True else str(0)}
        dictData.update({"class-id": classData})
        for line in self.listLine:
            lineData = str(line.startDirect[0]) + ";" + str(line.startDirect[1]) + ";" + str(line.endDirect[0]) + ";"  + str(line.endDirect[1]) + ";" + str(line.startLine[0]) + ";" + str(line.startLine[1]) + ";" + str(line.endLine[0]) + ";" + str(line.endLine[1])
            keyName = "line-crossing-" + line.name 
            dictData.update({keyName: lineData})
        sectionName = "line-crossing-stream-" + str(self.streamID)

        return sectionName, dictData

    def UpdatePropertyFromDict(self, sectionName, dictData):

        streamID = sectionName.split('-')[-1]
        self.streamID = streamID
        section = sectionName.split('-')[0]    
        if section == "line":
            self.RemoveAllLine()
            self.extended = True if dictData["extended"] == "1" or 1 else False
            self.enable =  True if dictData["enable"] == "1" or 1 else False
            
            if dictData["mode"] == "loose":
                self.mode = LOOSE
            elif dictData["mode"] == "balanced":
                self.mode = BALANCED
            elif dictData["mode"] == "strict":
                self.mode = STRICT
                
            classID = dictData["class-id"]
            self.availableClass = [int(id) for id in classID.split(";")]
            for index, value in enumerate(dictData.keys()):
                if value.split("-")[0] == "line":
                    lineObject = LineCross()
                    lineObject.name = value.split("-")[-1]
                    lineObject.ID = index
                    pointsData = dictData[value].split(";")
                    pointsData = [int(data) for data in pointsData]
                    lineObject.SetStartDirect = (pointsData[0], pointsData[1])
                    lineObject.SetEndDirect = (pointsData[2], pointsData[3])
                    lineObject.SetStartLine = (pointsData[4], pointsData[5])
                    lineObject.SetEndLine = (pointsData[6], pointsData[7])
                    self.AddLine(lineObject)
            #print("list line: {}".format(self.listLine[0].name))
            return self.enable, self.availableClass, len(self.listLine), self.mode, self.extended
        else:
            raise ValueError ("Section name must be 'direction'")


class Direction():

    def __init__(self, ID = 0, name = "Driect1", startPoint = (0,0), endPoint = (0,0), avaiClass = [], **kwargs):
        self.ID = ID
        self.name = name
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.avaiClass = avaiClass

    @property

    def SetName(self):
        return self.name

    @SetName.setter
    
    def SetName(self, name):
        self.name = name

    @property

    def SetID(self):
        return self.ID
    
    @SetID.setter

    def SetID(self, ID):
        self.ID = ID
    
    @property

    def SetStartPoint(self):
        return self.startPoint

    @SetStartPoint.setter

    def SetStartPoint(self, startPoint: tuple, **kwargs):
        self.startPoint = startPoint
    @property
    def SetEndPoint(self):
        return self.endPoint

    @SetEndPoint.setter
    def SetEndPoint(self, endPoint: tuple):
        self.endPoint = endPoint

    def __call__(self):
        print("Direction: %s" % self.name)

class DirectionConfig(ObjectConfig):

    def __init__(self, streamID = 0, streamName = "direction1", enable = True, mode= "balanced", **kwargs):
        
        super(DirectionConfig, self).__init__(streamID, streamName , enable)
        self.listDirection = []
        self.mode = mode

    def GetAllDirectionName(self):
        directionName = []

        for line in self.listDirection:
            directionName.append(line.name)
        return directionName

    def GetAllDirectionID(self):
        directionID = []
        
        for direction in self.listDirection:
            print("running")
            directionID.append(direction.ID)
    
        return directionID
    
    def AddDirection(self, direction: Direction):
        

        if isinstance(direction, Direction):
            if direction.ID not in self.GetAllDirectionID():
                self.listDirection.append(direction)

            else:
                raise ValueError("Direction with ID already exists")

        else:
            raise TypeError("Only except Direction type")


    def RemoveDirectionWithName(self ,name):

        if isinstance(name, str):
            index = self.GetAllDirectionName().index(name)
            self.listDirection.pop(index)

    """
        This function replace the current ROI with  a new ROI with the same name. It often used when the ROI has any change
        
        :param objectClass: The class of the object you want to add
        """


    def RemoveDirectionWithID(self,ID):
        index = self.GetAllDirectionID().index(ID)
        self.listDirection.pop(index)

    def RemoveAllDirection(self):
        self.listDirection.clear()

    def GetDirectionWithName(self, name):
        index = self.GetAllDirectionName().index(name)
        return self.listDirection[index]


    def UpdateDirection(self, nameOfDirection :str, newDirection: Direction, **kwargs):
        """
        This function replace the current Direction with  a new Direction with the same name. It often used when the ROI has any change
        
        :nameOfDirection: Name of the Direction needed to be updated
        :newROI: the new ROI which is used to replace the current ROI
        """
        if isinstance(newDirection, Direction):
            # direct = self.GetDirectionWithName(nameOfDirection)
            # direct = newDirection
            self.RemoveDirectionWithName(nameOfDirection)
            self.AddDirection(newDirection)


    def GetDirection(self, name: str):

        if isinstance(name, str):
            index = self.GetAllDirectionName().index(name)
            return self.listDirection[index]

    def Property2DictFormat(self):
        classData = ""
        for index, classObject in enumerate(self.availableClass):
            
            if index == len(self.availableClass) - 1:
                classData += str(classObject)
            else:
                classData += (str(classObject) + ";")

        dictData = {"enable":str(1) if self.enable == True else str(0)}
        dictData.update({"class-id": classData})
        dictData.update({"mode": self.mode})

        for  direct in self.listDirection:
            directionData = str(direct.startPoint[0]) + ";" + str(direct.startPoint[1]) + ";" + str(direct.endPoint[0]) + ";" + str(direct.endPoint[1])
            keyName = "direction-" + direct.name
            dictData.update({keyName: directionData})
        sectionName = "direction-detection-stream-" + str(self.streamID)

        return sectionName, dictData

    def UpdatePropertyFromDict(self, sectionName, dictData):

        streamID = sectionName.split('-')[-1]
        self.streamID = streamID
        section = sectionName.split('-')[0]    
        if section == "direction":
            self.RemoveAllDirection()
            self.enable =  True if dictData["enable"] == "1" or 1 else False
            try:
                self.mode = dictData["mode"]
            except:
                print("Cannot find 'mode' of Direction")
            classID = dictData["class-id"]
            self.availableClass = [int(id) for id in classID.split(";")]
            for index, value in enumerate(dictData.keys()):
                if value.split("-")[0] == "direction":
                    directObject = Direction()
                    directObject.name = value.split("-")[-1]
                    directObject.ID = index
                    pointsData = dictData[value].split(";")
                    pointsData = [int(data) for data in pointsData]
                    #print(pointsData[0])
                    directObject.SetStartPoint = (pointsData[0], pointsData[1])
                    directObject.SetEndPoint = (pointsData[2], pointsData[3])
                    self.AddDirection(directObject)
            return self.enable, self.availableClass, len(self.listDirection)
        else:
            raise ValueError ("Section name must be 'direction'")
            
    
    def __call__(self):

        print("Direction: %s" % self.streamName)


class ROI():

    def __init__(self, ID = 0, name = "ROI1", avaiClass = []):
        self.ID = ID
        self.name = name
        self.polygonPoint = []
        self.avaiClass = avaiClass
    
    @property
    def SetName(self):
        return self.name

    @SetName.setter

    def SetName(self, name):
        self.name = name

    @property

    def SetID(self):
        return self.ID

    @SetID.setter

    def SetID(self, ID):
        self.ID = ID
    #list Point ex.. [(23,45), (56,78),...]
    def SetAllPolygonPoint(self, listPoints: list):
        self.polygonPoint = listPoints

    def EditPolygonPoint(self, index, newVal):
        self.polygonPoint[index] = newVal

    def AddPolygonPoint (self, point):
        self.polygonPoint.append(point)

    def RemovePolygonPoint(self, index):
        self.polygonPoint.pop(index)
    
    def GetPolygonPoint (self):
        return self.polygonPoint

    def __call__(self):
        print("Polygon: %s" % self.name)

class ROIConfig(ObjectConfig):
    def __init__(self, streamID = 0, streamName = "ROI", enable = True, inverseROI = False, **kwargs):
        super(ROIConfig, self).__init__(streamID, streamName, enable)
        self.listROI = []
        self.inverseROI = inverseROI

    def GetAllROIName(self):
        listROIname = []
        for roi in self.listROI:
            listROIname.append(roi.name)

        return listROIname

    def GetAllROIID(self):
        listROIID = []
        for roi in self.listROI:
            listROIID.append(roi.ID)
        
        return listROIID


    def AddROI(self, roi: ROI,**kwargs):

        if isinstance(roi, ROI):
            if roi.name not in self.GetAllROIName():
                self.listROI.append(roi)
            
            else:
                raise ValueError ("ROI with Name have already been added")
        
        else:
            raise TypeError ("Only except ROI type")

    def RemoveROIWithName(self ,name):

        if isinstance(name, str):
            index = self.GetAllROIName().index(name)
            self.listROI.pop(index)

    def GetROIWithName(self, name):
        index = self.GetAllROIName().index(name)
        print(self.listROI[index])
        return self.listROI[index]


    def UpdateROI(self, nameOfROI :str, newROI: ROI, **kwargs):
        """
        This function replace the current ROI with  a new ROI with the same name. It often used when the ROI has any change
        
        :nameOfROI: Name of the ROI needed to be updated
        :newROI: the new ROI which is used to replace the current ROI
        """
        print(newROI.GetPolygonPoint())
        if isinstance(newROI, ROI):
            self.RemoveROIWithName(nameOfROI)
            self.AddROI(newROI)
            
            # roi = self.GetROIWithName(nameOfROI)
            # print(roi)
            # roi = newROI
            
            # print(roi.GetPolygonPoint())
            # print(self.GetROIWithName(nameOfROI).GetPolygonPoint())
            


    def RemoveROIWithID(self,ID):
        index = self.GetAllROIID().index(ID)
        self.listROI.pop(index)

    def RemoveAllROI(self):
        self.listROI.clear()

    def Property2DictFormat(self):
        """
        The function takes the data from the class and converts it into a dictionary format
        :return: A tuple of the section name and the dictionary data.
        """
        classData = ""
        for index, classObject in enumerate(self.availableClass):
            
            if index == len(self.availableClass) - 1:
                classData += str(classObject)
            else:
                classData += (str(classObject) + ";")

        dictData = {"enable":str(1) if self.enable == True else str(0), "inverse-roi": str(1) if self.inverseROI == True else str(0)}
        dictData.update({"class-id": classData})

        for  ROI_data in self.listROI:
            polygonData = ""

            for index, point in enumerate(ROI_data.GetPolygonPoint()):
                x = point[0]
                y = point[1]
                if point[0] >= maxX:
                    x = 1919
                if point[1] >= maxY:
                    y = 1079
                pointData = str(x) + ";" + str(y)
                if index == len(ROI_data.GetPolygonPoint()) - 1:
                    polygonData += pointData
                else:
                    polygonData += (pointData + ";")
            keyROIName = "roi-" + str(ROI_data.name)
            dictData.update({keyROIName: polygonData})
        sectionName = "roi-filtering-stream-" + str(self.streamID)
        return sectionName, dictData

    def UpdatePropertyFromDict(self, sectionName, dictData):

        streamID = sectionName.split('-')[-1]
        self.streamID = streamID
        section = sectionName.split('-')[0]
        
        self.RemoveAllROI()
        if section == "roi":
            self.enable =  True if dictData["enable"] == "1" or 1 else False
            classID = dictData["class-id"]
            self.availableClass = [int(id) for id in classID.split(";")]
            for index, value in enumerate(dictData.keys()):
                if value.split("-")[0] == "roi":
                    ROIobject = ROI()
                    ROIobject.name = value.split("-")[-1]
                    ROIobject.ID = index
                    pointsData = dictData[value].split(";")
                    pointsData = [int(data) for data in pointsData]
                    listPoints = []
                    for index, (x,y) in enumerate(zip(pointsData, pointsData[1:])):
                        if index %2 == 0:
                            ROIobject.AddPolygonPoint((x,y))
                        listPoints.append((x,y))
                    self.AddROI(ROIobject)

        else:
            raise ValueError ("Section name must be 'roi'")

class OverCrowdingConfig(ObjectConfig):
    def __init__(self, streamID = 0, streamName = "ROI", enable = True, objectThreshold = 10, **kwargs):
        super(OverCrowdingConfig, self).__init__(streamID, streamName, enable)
        self.listROI = []
        self.objectThreshold = objectThreshold

    @property
    def SetObjectThreadhold(self):
        return self.objectThreshold

    @SetObjectThreadhold.setter

    def SetObjectThreadhold(self, value):
        self.objectThreshold = value

    def GetAllROIName(self):
        listROIname = []
        for roi in self.listROI:
            listROIname.append(roi.name)

        return listROIname

    def GetAllROIID(self):
        listROIID = []
        for roi in self.listROI:
            listROIID.append(roi.ID)
        
        return listROIID

    def AddROI(self, roi: ROI,**kwargs):
        """
        > This function adds a ROI object to the list of ROIs in the image
        
        :param roi: ROI
        :type roi: ROI
        """

        if isinstance(roi, ROI):
            if roi.ID not in self.GetAllROIID():
                self.listROI.append(roi)
            
            else:
                raise ValueError ("ROI with ID have already been added")
        
        else:
            raise TypeError ("Only except ROI type")

    def RemoveROIWithName(self ,name):
        """
        > This function removes the ROI with the name `name` from the list of ROIs
        
        :param name: The name of the ROI
        """
        if isinstance(name, str):
            index = self.GetAllROIName().index(name)
            self.listROI.pop(index)
    
    def GetROIWithName(self, name):
        index = self.GetAllROIName().index(name)
        return self.listROI[index]


    def UpdateROI(self, nameOfROI :str, newROI: ROI, **kwargs):
        """
        This function replace the current ROI with  a new ROI with the same name. It often used when the ROI has any change
        
        :param objectClass: The class of the object you want to add
        """
        if isinstance(newROI, ROI):
            self.RemoveROIWithName(nameOfROI)
            self.AddROI(newROI)
            # roi = self.GetROIWithName(nameOfROI)
            # roi = newROI

   

    def RemoveROIWithID(self,ID):
        """
        It removes the ROI with the given ID from the list of ROIs
        
        :param ID: The ID of the ROI you want to remove
        """
        index = self.GetAllROIID().index(ID)
        self.listROI.pop(index)

    def RemoveAllROI(self):
        self.listROI.clear()

    def Property2DictFormat(self):
        """
        The function takes the data from the class and converts it into a dictionary format
        :return: A tuple of the section name and the dictionary data.
        """
        classData = ""
        for index, classObject in enumerate(self.availableClass):
            
            if index == len(self.availableClass) - 1:
                classData += str(classObject)
            else:
                classData += (str(classObject) + ";")

        dictData = {"enable":str(1) if self.enable == True else str(0), "object-threshold": str(self.objectThreshold)}
        dictData.update({"class-id": classData})

        for  ROI_data in self.listROI:
            polygonData = ""

            for index, point in enumerate(ROI_data.GetPolygonPoint()):
                pointData = str(point[0]) + ";" + str(point[1])
                if index == len(ROI_data.GetPolygonPoint()) - 1:
                    polygonData += pointData
                else:
                    polygonData += (pointData + ";")
            keyROIName = "roi-" + str(ROI_data.name)
            dictData.update({keyROIName: polygonData})
        sectionName = "overcrowding-stream-" + str(self.streamID)
        return sectionName, dictData

    def UpdatePropertyFromDict(self, sectionName, dictData):

        streamID = sectionName.split('-')[-1]
        self.streamID = streamID
        section = sectionName.split('-')[0]   
        if section == "overcrowding":
            self.RemoveAllROI()
            self.enable =  True if dictData["enable"] == "1" or 1 else False
            self.objectThreshold = int(dictData["object-threshold"])
            classID = dictData["class-id"]
            self.availableClass = [int(id) for id in classID.split(";")]
            for index, value in enumerate(dictData.keys()):
                if value.split("-")[0] == "roi":
                    ROIobject = ROI()
                    ROIobject.name = value.split("-")[-1]
                    ROIobject.ID = index
                    pointsData = dictData[value].split(";")
                    pointsData = [int(data) for data in pointsData]
                    for index, (x,y) in enumerate(zip(pointsData, pointsData[1:])):
                        if index % 2 == 0:
                            ROIobject.AddPolygonPoint((x,y))
                    self.AddROI(ROIobject)
            return self.enable, self.availableClass, len(self.listROI), self.objectThreshold

        else:
            raise ValueError ("Section name must be 'roi'")


class PropertyConfig():
    def __init__(self, width = 1920, height = 1080, OSDmode = 0, font = 8, enable = True, **kwargs):
        self.width = width
        self.height = height
        self.OSDmode = OSDmode
        self.font = font
        self.enable = enable

    def SetEnableState(self, state):
        self.enable = state

    def SetSize(self, width, height, **kwargs):
        self.width = width
        self.height = height

    def SetOSDmode(self, mode):
        self.OSDmode = mode

    def SetFont(self, font ):
        self.font = font

    def Property2DictFormat(self):
        """
        It converts the class object to a dictionary format
        :return: A tuple of the section name and the dictionary of the data.
        """
        print("state: {}".format(self.enable))
     
        dictData = {"enable": str(1) if self.enable == True else str(0), "config-width":str(self.width), "config-height": str(self.height),
                     "osd-mode": str(self.OSDmode), "display-font-size": str(self.font)}

        sectionName = "property"
        return sectionName, dictData

    def UpdatePropertyFromDict(self, sectionName, dictData):
        """
        It takes a dictionary and a section name, and if the section name is "property", it updates the
        object's properties with the values in the dictionary
        
        :param sectionName: The name of the section in the config file
        :param dictData: A dictionary containing the data to be updated
        :return: The width, height, OSDmode, font, and enable values are being returned.
        """

        if sectionName == "property":
            self.width = int(dictData["config-width"])
            self.height = int(dictData["config-height"])
            self.OSDmode = int(dictData["osd-mode"])
            self.font = int(dictData["display-font-size"])
            self.enable = True if dictData["enable"] == "1" or 1 else False
            return self.width, self.height, self.OSDmode, self.font, self.enable
        else:
            raise ValueError ("Section name must be 'property'")

# class test_module(unittest.TestCase):
#     def __init__(self):
#         super(test_module, self).__init__()
#         roi1 = ROI(ID = 5, name = "roi1")
#         roi2 = ROI(ID = 6, name = "enter")
#         roi1.AddPolygonPoint((10,20))
#         roi1.AddPolygonPoint((60,20))
#         roi2.AddPolygonPoint((69,89))
#         over_config = OverCrowdingConfig(streamID = 1)
#         over_config.AddROI(roi1)
#         over_config.AddROI(roi2)
#         over_config.AddClass(3)
#         over_config.AddClass(2)
#         roi_config = ROIConfig(streamID = 2)
#         roi_config.AddROI(roi1)
#         roi_config.AddROI(roi2)
#         roi_config.AddClass(6)
#         roi_config.AddClass(5)
#         readOverCrowd = Controller.ParseTXTConfig("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/lib/test3.txt")
#         readROI = Controller.ParseTXTConfig("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/lib/test4.txt")
#         data = readOverCrowd.ReadData()
#         data2 = readROI.ReadData()
#         ROISection, ROIVal = roi_config.Property2DictFormat()
#         outTest = ("overcrowding-stream-1",{"enable":1, "object-threshold": 10, "class-id": "3;2","roi-roi1": "10;20;60;20", "roi-enter": "69;89"})
#         #self.assertEqual(over_config.Property2DictFormat(), ("overcrowding-stream-1",readOverCrowd.GetSection("overcrowding-stream-1")))
#         #self.assertEqual(roi_config.Property2DictFormat(), ("roi-filtering-stream-2",readROI.GetSection("roi-filtering-stream-2")))
#         directConfig = DirectionConfig(streamID = 4)
#         direct1 = Direction(ID = 2, name = "direct1", startPoint = (4,15), endPoint = (6,9))
#         direct2 = Direction(ID = 3, name = "direct2", startPoint = (16,15), endPoint = (7,9))
#         directConfig.AddDirection(direct1)
#         directConfig.AddDirection(direct2)
#         directConfig.AddClass(8)
#         directConfig.AddClass(9)
#         readDirection = Controller.ParseTXTConfig("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/lib/test_direct.txt")
#         data = readDirection.ReadData()
#         directSection, directVal = directConfig.Property2DictFormat()
#         #self.assertEqual(directConfig.Property2DictFormat(), ("direction-detection-stream-4", readDirection.GetSection("direction-detection-stream-4")))
#         lineConfig = LineCrossConfig(streamID = 5)
#         line1 = LineCross(ID = 2, name = "line_1", startLine = (45,0), endLine = (0,89), startDirect = (13,0), endDirect = (11,2))
#         line2 = LineCross(ID = 3, name = "line_2", startLine = (45,18), endLine = (1,89), startDirect = (13,12), endDirect = (11,3))
#         lineConfig.AddLine(line1)
#         lineConfig.AddLine(line2)
#         lineConfig.AddClass(3)
#         lineConfig.AddClass(4)
#         readLine = Controller.ParseTXTConfig("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/lib/test_line.txt")
#         data = readLine.ReadData()
#         #self.assertEqual(lineConfig.Property2DictFormat(), ("line-crossing-stream-5", readLine.GetSection("line-crossing-stream-5")))
#         lineSection, lineVal = lineConfig.Property2DictFormat()
#         readProperty = Controller.ParseTXTConfig("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/lib/test_property.txt")
#         readProperty.ReadData()
#         propertyConfig = PropertyConfig(width = 1920, height = 1080, OSDmode = 2, font = 12)
#         #self.assertEqual(propertyConfig.Property2DictFormat(), ("property", readProperty.GetSection("property")))
#         propertySection, propertyVal = propertyConfig.Property2DictFormat()
#         overCrowSection, overCrowVal = over_config.Property2DictFormat()
#         configAnalys = Controller.ParseTXTConfig("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/lib/config_analystic.txt")
#         # configAnalys.AddSection(propertySection, propertyVal)
#         # configAnalys.AddSection(lineSection, lineVal)
#         # configAnalys.AddSection(directSection, directVal)
#         # configAnalys.AddSection(ROISection, ROIVal)
#         # configAnalys.AddSection(overCrowSection, overCrowVal)
#         # configAnalys.WriteData()
#         configAnalys.ReadData()
#         getProperty = configAnalys.GetSection("property")
#         getROI = configAnalys.GetSection("roi-filtering-stream-2")
#         #roi_config.UpdatePropertyFromDict("roi-filtering-stream-2", getROI)
#         #self.assertEqual(roi_config.UpdatePropertyFromDict("roi-filtering-stream-2", getROI), (True, [6,5], 2))
#         getDirect = configAnalys.GetSection("direction-detection-stream-4")
#         self.assertEqual(directConfig.UpdatePropertyFromDict("direction-detection-stream-4", getDirect), (True, [8,9], 2))
#         getLine = configAnalys.GetSection("line-crossing-stream-5")
#         self.assertEqual(lineConfig.UpdatePropertyFromDict("line-crossing-stream-5",getLine), (True, [3,4], 2,BALANCED, False))
#         getCrow = configAnalys.GetSection("overcrowding-stream-1")
#         self.assertEqual(over_config.UpdatePropertyFromDict("overcrowding-stream-1",getCrow), (True, [3,2], 2, 10))
#         #self.enable, self.availableClass, len(self.listROI), self.objectThreshold

#         print("Test Done All module")

        
        
# if __name__ == "__main__":

#     mo = test_module()
#     print("ok")
    
    


    
    



 

        


        

        
             
        



    

