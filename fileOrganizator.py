import os
import sys
import ssl
import mmap
import hashlib
import certifi
import geopy.geocoders
from pathlib import Path
from ExifTool import ExifTool
from copyFiles import CopyFiles
from geopy.geocoders import Nominatim

class FileOrganizator:
    errorTimesToTry = 2
    ctx = ssl.create_default_context(cafile=certifi.where())
    geopy.geocoders.options.default_ssl_context = ctx
    geolocator = Nominatim(user_agent="FileOrganizator")
    geoDic = {}
    geoDicNew = {}
    geoGPSFile = "geoGPSFile.txt"

    def __init__(self, errorTimesToTry):
        self.errorTimesToTry = errorTimesToTry
    
    def getFileType(self,fileParam):
        filename, file_extension = os.path.splitext(fileParam)
        print(filename)
        return file_extension

    def createMD5Checksum(self, fileParam):
        return hashlib.md5(open(fileParam,'rb').read()).hexdigest()

    def modifyDateTime(self, dateTime, addTime):
        dateTimeFormated = dateTime.replace(':','_')
        if addTime:
            dateTimeFormated = dateTimeFormated.replace(' ','_')
        else:
            dateTimeFormated = dateTimeFormated.partition(" ")[0]
        return dateTimeFormated
    
    def getGPSLocationPath(self, GPSPosition):
        locationRet = ""
        if not GPSPosition in self.geoDic.keys():
            fullLocationDict = dict(self.geolocator.reverse(GPSPosition, exactly_one=True).raw)
            locationDict = dict(fullLocationDict['address'])
            locationRet = locationDict['county'] + '_' + locationDict['state'] +'_' + locationDict['country_code']
            self.geoDic[GPSPosition] = locationRet 
            self.geoDicNew[GPSPosition] = locationRet
        else:
            locationRet = self.geoDic[GPSPosition]
        return locationRet
    
    def saveGeoGPSDic(self):
        saveFileGPS = open("data.pkl", "ab")
        pickle.dump(geoDicNew, saveFileGPS)
        saveFileGPS.close()
    
    def loadGeoGPSDIc(self):
        gpsFile = open(self.geoGPSFile,"r")
        self.geoDic = gpsFile.read()
        dictionary = ast.literal_eval(self.geoDic)
        gpsFile.close()
    
    def generatePathPatternToCopy(self, jsonResult):
        dataDict = dict(jsonResult[0])
        fullLocationDict = ""
        imageSize = ""
        pathPattern = ""
        if not 'ExifTool:Error' in dataDict:
            FileType = dataDict['File:FileType']
            if 'Composite:GPSPosition' in dataDict:
                fullLocationDict = self.getGPSLocationPath(dataDict['Composite:GPSPosition'])
            if 'EXIF:DateTimeOriginal' in dataDict:
                dateTimeFormated = dataDict['EXIF:DateTimeOriginal']
            else:
                dateTimeFormated = dataDict['File:FileModifyDate']
            dateTimeFormated = self.modifyDateTime(dateTimeFormated, False)
            if 'File:ImageWidth' in dataDict and 'File:ImageHeight' in dataDict:
                imageSize = str(dataDict['File:ImageWidth']) + "_X_" + str(dataDict['File:ImageHeight']) 
            pathPattern = FileType + os.path.sep + dateTimeFormated 
            if 'Composite:GPSPosition' in dataDict:
                pathPattern = pathPattern + os.path.sep + fullLocationDict
            if 'File:ImageWidth' in dataDict and 'File:ImageHeight' in dataDict:
                pathPattern = pathPattern + os.path.sep + imageSize
        elif 'File:FileName' in dataDict and 'File:FileModifyDate' in dataDict:
            fileName = str(dataDict['File:FileName'])
            index = int(fileName.rfind(".")) + 1
            fileType = fileName[index:]
            dateTimeFormated = self.modifyDateTime(dataDict['File:FileModifyDate'], False)
            pathPattern = fileType + os.path.sep + dateTimeFormated
        return pathPattern
    
    def checkDir(self, newPathParam, homePathParam):
        if not bool(newPathParam):
            return False
        newPath = homePathParam + os.path.sep + newPathParam
        if not os.path.isdir(newPath):
            os.makedirs(newPath, exist_ok=True)
        return os.path.isdir(newPath)

    def moveAndOrganizeEachFile(self, pathParam):
        filesAndDir = CopyFiles().getListFilesAndDir(pathParam)
        goToDir = str(Path.home()) + os.path.sep + "Organized"
        self.fileOrganizator(filesAndDir[0], pathParam, goToDir)
        for activeDir in filesAndDir[1]:
            newPathParam = pathParam + os.path.sep + activeDir
            self.moveAndOrganizeEachFile(newPathParam)
    
    def fileOrganizator(self, filesParam, pathFileOrgParam, goToDir):
        for fileActive in filesParam:
            fileMetadataActive = pathFileOrgParam + os.path.sep + fileActive
            pathToCopy = self.generatePathPatternToCopy(ExifTool().get_metadata(fileMetadataActive))
            newPathFile = goToDir + os.path.sep + pathToCopy + os.path.sep + fileActive
            if self.checkDir(pathToCopy, goToDir):
                if os.path.isfile(newPathFile):
                    newPathFileCopy = newPathFile_ + str(int(round(time.time() * 1000)))
                    os.rename(fileMetadataActive, newPathFileCopy)
                else:
                    os.rename(fileMetadataActive, newPathFile)
    
    def compareMD5(self):
        try:
            filePath = str(CopyFiles().getHomeBridgePath()) + os.path.sep + str(CopyFiles().MD5File)
            filePathCopied = str(filePath)+str(CopyFiles().LOCAL_STR)
            succesFile = str(CopyFiles().getHomeBridgePath()) + os.path.sep + str(CopyFiles().succesFile)
            if os.path.exists(succesFile):
                os.remove(succesFile)
            with open(str(filePath)) as f:
                myList = list(f)
                with open(filePathCopied) as g:
                    s = mmap.mmap(g.fileno(), 0, access=mmap.ACCESS_READ) 
                    with open(str(succesFile), "a") as fp:
                        for elementActive in myList:
                            elementActive = elementActive.rstrip("\n")
                            if s.find(bytes(elementActive,  encoding='utf8')) == -1:
                                fp.write(elementActive)
        finally:
            f.close()
            g.close()
            fp.close()
            s.close()

    def startFileOrganizator(self):
        self.loadGeoGPSDic()
        CopyFiles().md5CheckFile(CopyFiles().getListFilesAndDir(CopyFiles().getHomeBridgePath()),CopyFiles().LOCAL_STR)
        self.compareMD5()
        #CopyFiles().sendAFile(CopyFiles().getHomeBridgePath() + os.path.sep + CopyFiles().succesFile)
        self.moveAndOrganizeEachFile(CopyFiles().getHomeBridgePath())
        self.saveGeoGPSDic()
        
p1 = FileOrganizator(2)
p1.startFileOrganizator()