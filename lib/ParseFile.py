import unittest
import os
import glob
import sys
import configparser
import yaml
from yaml.loader import SafeLoader

class ParseDeepStreamConfig():

    def __init__(self, configFile, **kwargs):
        self.allConfigData = {}
        self.configFile = configFile
    
    def GetSection(self, sectionName):
        return self.allConfigData[sectionName]

    def GetKeyVal(self, sectionName, key, **kwargs):
        return self.allConfigData[sectionName][key]

    def SetSection(self, sectionName, newSectionValue, **krargs):
        self.allConfigData[sectionName] = newSectionValue
    
    def SetKeyValue(self, section ,key, newValue, **krargs):
        self.allConfigData[section][key] = newValue

    def RemoveSection(self, sectionName):
        self.allConfigData.pop(sectionName)
        
    def RemoveKeyVal(self,section, key, **kwargs):
        self.allConfigData[section].pop(key)


class ParseTXTConfig(ParseDeepStreamConfig):

    def __init__(self, configFile, **kwargs):
        
        super(ParseTXTConfig, self).__init__(configFile)
        self.configParser = configparser.ConfigParser()
        self.allConfigData = {}
    def AddFullData(self,data):
        for k,v in data.items():
           self.AddSection(k,v)
        
    
    def AddDictData(self, dictData):
        self.configParser.read_dict(dictData)

    def AddSection(self,section,value):
        self.configParser[section] = value
        self.allConfigData[section] = value

    def AddKeyValue(self, section, key,value):
        self.allConfigData[section][key] = value
        self.configParser[section][key] = value
        
    def ReadData(self):
        self.configParser.read(self.configFile)
        self.allConfigData = self.configParser._sections
        print(type(self.allConfigData))
        return self.allConfigData
        
    def WriteData(self):

        with open(self.configFile, 'w') as configfile:
            self.configParser.write(configfile)
            

    def ConvertYML(self):
        
        rootName = self.configFile.split('.')[0]
        saveName = rootName + ".yml"

        for key,first_values in self.allConfigData.items():
            for second_key, second_value in first_values.items():
                try: 
                    self.allConfigData[key][second_key] = float(second_value)
                    #print("ok")
                except:
                    pass

        with open(saveName, 'w') as configfile:
            yaml.dump(self.allConfigData, configfile, sort_keys=False, default_flow_style=False)

  
    def returnVal(self):
        return 7

class ParseYMLConfig(ParseDeepStreamConfig):

    def __init__(self, configFile, **kwargs):
        super().__init__(configFile)
        self.allConfigData = {}
    def AddFullData(self,data:dict):
        for k,v in data.items():
            self.allConfigData[k] = v

        

    def AddSection(self,section,value):
        self.allConfigData[section] = value

    def AddKeyValue(self, section, key,value):
        self.allConfigData[section][key] = value

    def ReadData(self):

        with open(self.configFile) as f:

            self.allConfigData = yaml.load(f, Loader=SafeLoader)
            return self.allConfigData

    def WriteData(self):
        with open(self.configFile, 'w') as configfile:
            yaml.dump(self.allConfigData, configfile, sort_keys=False, default_flow_style=False)

    def ConvertTXT(self, **kwargs):

        rootName = self.configFile.split('.')[0]
        saveName = rootName + ".txt"
        configParser = configparser.ConfigParser()
        configParser._sections = self.allConfigData
        
        with open(saveName, 'w') as configfile:
            configParser.write(configfile)


class UnitTest(unittest.TestCase):
    def __init__(self):
       super().__init__()

    def Test_ReadTXT(self, fileName):

        parseTXT = ParseTXTConfig(fileName)
   
        data = parseTXT.ReadData()
        parseTXT.AddSection("class-attrs-all-data",{"data": 8})
        parseTXT.WriteData()
        parseTXT.ConvertYML()
        outData = {"class-attrs-all": {"pre-cluster-threshold": '0.2', "eps": '0.7', "minboxes": '1'}, "class-attrs-0": {"pre-cluster-threshold": '0.05', "eps":'0.7', "dbscan-min-score":'0.95'}}
        out = '0.2'
        outData = {"BaseConfig": {"minDetectorConfidence": 0}, "TargetManagement": {"preserveStreamUpdateOrder": 0, "maxTargetsPerStream": 150}}
        self.assertEqual(parseTXT.ReadData(), outData)
        #self.assertEqual(parseYML.ReadData(), outData)
        # parseYML.AddKeyValue("BaseConfig", "minDetectorConfidence_mu", 18)
        # parseYML.WriteData()
        # parseYML.ConvertTXT()
        #self.assertEqual(parseTXT.GetKeyVal("class-attrs-all", "pre-cluster-threshold"), out)

if __name__ == "__main__":
     test = UnitTest()
     test.Test_ReadTXT("/home/rtc/Documents/Create_keypoint_dataset_app/Ketpoint_annotation_app/main_code/Config_Deepstream_code/test2.txt")
   




    

