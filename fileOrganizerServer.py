import os
import ssl
import mmap
import time
import pysftp
import certifi
import hashlib
import geopy.geocoders
from pathlib import Path
from ExifTool import ExifTool
from geopy.geocoders import Nominatim


class FileOrganizatorServer:

    errorTimesToTry = 2
    geoDic = {}
    geoDicNew = {}
    usrNameMac = "agus"
    LOCAL_STR = "Local"
    MD5File = "MD5.check"
    geoGPSFile = "organizeData/geoGPSFile.txt"
    succesFile = "MD5Result.check"
    remoteHomeUnix = "/Users/agus/Bridge"
    geolocator = Nominatim(user_agent="FileOrganizator")
    ctx = ssl.create_default_context(cafile=certifi.where())
    privateKeyToMac = "C:\\Users\\zid_0\\.ssh\\id_rsa.fileOrgW"

    geopy.geocoders.options.default_ssl_context = ctx

    def __init__(self, errorTimesToTry):
        self.errorTimesToTry = errorTimesToTry

    # Obtiene el home path de Bridge
    def getHomeBridgePath(self):
       # return str(Path.home()) + os.path.sep + "Bridge"
       return "H:\\Bridge"

    # Load file who has all info from GPS
    def loadGeoGPSDic(self):
        with open(self.geoGPSFile) as f:
            for line in f:
                (key, val) = line.split(":")
                self.geoDic[key] = val
        f.close

    # Genera un MD5 de un archivo
    def createMD5Checksum(self, fileParam):
        return hashlib.md5(open(fileParam, 'rb').read()).hexdigest()

    # Send files
    def sendAFile(self, pathParam):
        try:
            with pysftp.Connection(self.usrNameMac, username=self.usrNameMac, private_key=self.privateKeyToMac) as sftp:
                with sftp.cd(self.remoteHomeUnix):
                    sftp.put(pathParam)
        finally:
            sftp.close()

    # Check the file that has all MD5 codes
    def md5CheckFile(self, listFilesParam, extend):
        home = self.getHomeBridgePath()
        homeMD5File = str(home) + str(os.path.sep) + \
            str(self.MD5File) + str(extend)
        if os.path.exists(homeMD5File):
            os.remove(homeMD5File)
        try:
            with open(str(homeMD5File), "a") as fp:
                for i in listFilesParam[0]:
                    activeFile = str(home) + str(os.path.sep) + i
                    fp.write(str(i) + "," +
                             str(self.createMD5Checksum(activeFile))+"\n")
                fp.close()
        finally:
            fp.close()

    # Obtiene una lista de Archivos y directorios
    def getListFilesAndDir(self, path):
        files = []
        directory = []
        dirP = []
        for (dirpath, dirnames, filenames) in os.walk(path):
            files.extend(filenames)
            directory.extend(dirnames)
            dirP.extend(dirpath)
            break
        return files, directory, dirP

    # Modify date time to used in a Path
    def modifyDateTime(self, dateTime, addTime):
        dateTimeFormated = dateTime.replace(':', '_')
        if addTime:
            dateTimeFormated = dateTimeFormated.replace(' ', '_')
        else:
            dateTimeFormated = dateTimeFormated.partition(" ")[0]
        return dateTimeFormated

    # Compare MD5 file
    def compareMD5(self):
        try:
            filePath = str(self.getHomeBridgePath()) + \
                os.path.sep + str(self.MD5File)
            filePathCopied = str(filePath)+str(self.LOCAL_STR)
            succesFile = str(self.getHomeBridgePath()) + \
                os.path.sep + str(self.succesFile)
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

    # Generate path and pattern to copy
    def generatePathPatternToCopy(self, jsonResult):
        dataDict = dict(jsonResult[0])
        fullLocationDict = ""
        imageSize = ""
        pathPattern = ""
        if not 'ExifTool:Error' in dataDict:
            FileType = dataDict['File:FileType']
            if 'Composite:GPSPosition' in dataDict:
                fullLocationDict = self.getGPSLocationPath(
                    dataDict['Composite:GPSPosition'])
            if 'EXIF:DateTimeOriginal' in dataDict:
                dateTimeFormated = dataDict['EXIF:DateTimeOriginal']
            else:
                dateTimeFormated = dataDict['File:FileModifyDate']
            dateTimeFormated = self.modifyDateTime(dateTimeFormated, False)
            if 'File:ImageWidth' in dataDict and 'File:ImageHeight' in dataDict:
                imageSize = str(dataDict['File:ImageWidth']) + \
                    "_X_" + str(dataDict['File:ImageHeight'])
            pathPattern = FileType + os.path.sep + dateTimeFormated
            if 'Composite:GPSPosition' in dataDict:
                pathPattern = pathPattern + os.path.sep + fullLocationDict
            if 'File:ImageWidth' in dataDict and 'File:ImageHeight' in dataDict:
                pathPattern = pathPattern + os.path.sep + imageSize
        elif 'File:FileName' in dataDict and 'File:FileModifyDate' in dataDict:
            fileName = str(dataDict['File:FileName'])
            index = int(fileName.rfind(".")) + 1
            fileType = fileName[index:]
            dateTimeFormated = self.modifyDateTime(
                dataDict['File:FileModifyDate'], False)
            pathPattern = fileType + os.path.sep + dateTimeFormated
        return pathPattern

    # Check if the dir exist
    def checkDir(self, newPathParam, homePathParam):
        if not bool(newPathParam):
            return False
        newPath = homePathParam + os.path.sep + newPathParam
        if not os.path.isdir(newPath):
            os.makedirs(newPath, exist_ok=True)
        return os.path.isdir(newPath)

    # File Organizator
    def fileOrganizator(self, filesParam, pathFileOrgParam, goToDir):
        for fileActive in filesParam:
            fileMetadataActive = pathFileOrgParam + os.path.sep + fileActive
            pathToCopy = self.generatePathPatternToCopy(
                ExifTool().get_metadata(fileMetadataActive))
            newPathFile = goToDir + os.path.sep + pathToCopy + os.path.sep + fileActive
            if os.path.isfile(newPathFile):
                index = int(fileActive.rfind(".")) + 1
                fileType = fileActive[index:]
                fileName = fileActive[:int(index - 1)]
                newPathFile = goToDir + os.path.sep + \
                    pathToCopy + os.path.sep + fileName + "_COPY_"
                newPathFile = newPathFile + \
                    str(hex(int(round(time.time() * 1000)))
                        ).upper() + "." + fileType
            if self.checkDir(pathToCopy, goToDir):
                os.rename(fileMetadataActive, newPathFile)

    # Get GPS Location and create a Path
    def getGPSLocationPath(self, GPSPosition):
        locationRet = ""
        if not GPSPosition in self.geoDic.keys():
            fullLocationDict = dict(self.geolocator.reverse(
                GPSPosition, exactly_one=True).raw)
            locationDict = dict(fullLocationDict['address'])
            locationRet = locationDict['county'] + '_' + \
                locationDict['state'] + '_' + locationDict['country_code']
            self.geoDic[GPSPosition] = locationRet
            self.geoDicNew[GPSPosition] = locationRet
        else:
            locationRet = str(self.geoDic[GPSPosition]).strip()
        return locationRet

    # Move and organize all files
    def moveAndOrganizeEachFile(self, pathParam):
        filesAndDir = self.getListFilesAndDir(pathParam)
        goToDir = str(Path.home()) + os.path.sep + "Organized"
        self.fileOrganizator(filesAndDir[0], pathParam, goToDir)
        for activeDir in filesAndDir[1]:
            newPathParam = pathParam + os.path.sep + activeDir
            self.moveAndOrganizeEachFile(newPathParam)

    # Save GPS dictionary
    def saveGeoGPSDic(self):
        with open(self.geoGPSFile, "a") as saveFileGPS:
            for key, value in self.geoDicNew.items():
                saveFileGPS.write('%s:%s\n' % (key, value))
        saveFileGPS.close()

    # start entry point
    def startFileOrganizator(self):
        self.loadGeoGPSDic()
        self.md5CheckFile(self.getListFilesAndDir(
            self.getHomeBridgePath()), self.LOCAL_STR)
        self.compareMD5()
        self.sendAFile(self.getHomeBridgePath() +
                       os.path.sep + self.succesFile)
        self.moveAndOrganizeEachFile(self.getHomeBridgePath())
        self.saveGeoGPSDic()

foS = FileOrganizatorServer(2)
foS.startFileOrganizator()