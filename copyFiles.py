import os
import py7zr
import pysftp
import hashlib
from pathlib import Path

class CopyFiles(object):
    remoteHomeWin = "C:\\Users\\Agus\\Bridge"
    remoteHomeUnix = "/Users/agus/Bridge"
    succesFile = "MD5Result.check"
    MD5File = "MD5.check"
    usrName = "agus"
    passw = "ajalas"
    host = "hostname"
    LOCAL_STR = "Local"
#cliente usara este metodo
#envia los archivos con SFTP remotamente
    def sendFiles(self, filesParam):
        homepath = self.getHomeBridgePath()
        try:
            with pysftp.Connection(self.host, username=self.usrName, password=self.passw) as sftp:
                with sftp.cd(self.remoteHomeWin):
                   for activeFile in filesParam:
                       fileTosend = homepath + os.path.sep + activeFile
                       sftp.put(fileTosend)
        finally:
            sftp.close()
#Este codigo lo executa el cliente quien enviara la info   
    def clientExecute(self):
        homepath = self.getHomeBridgePath()
        resultFilePath = homepath + os.path.sep + self.succesFile
        if os.path.exists(resultFilePath):
            try:
             with open(resultFilePath) as fp:
                 for cnt, line in enumerate(fp):
                     print("Line {}: {}".format(cnt, line))
                     rmLineFilePath = homepath + os.path.sep + line
                     if os.path.exists(rmLineFilePath):
                        os.remove(rmLineFilePath)
            finally:
                fp.close()
                os.remove(resultFilePath)
        listFileDir = self.getListFilesAndDir(homepath)
        for activeDir in listFileDir[1]:
            try:
                with py7zr.SevenZipFile(activeDir + '.7z', 'w') as archive:
                    archive.writeall(homepath + os.path.sep + activeDir, 'base')
                    listFileDir[0].append(archive.filename)
            finally:
                archive.close()
        self.md5CheckFile(listFileDir[0],"")
        listFileDir[0].append(self.MD5File)
        self.sendFiles(listFileDir[0])

#compartido
#genera un archivo con los MD5 de una lista de archivos
    def md5CheckFile(self, listFilesParam, extend):
        home = self.getHomeBridgePath()
        homeMD5File = str(home) + str(os.path.sep) + str(self.MD5File) + str(extend)
        if os.path.exists(homeMD5File):
            os.remove(homeMD5File)
        try:
            with open(str(homeMD5File), "a") as fp:
                for i in listFilesParam[0]:
                    activeFile = str(home) + str(os.path.sep) + i
                    fp.write(str(i) + "," + str(self.createMD5Checksum(activeFile))+"\n")
                fp.close()
        finally:
            fp.close()
#Genera un MD5 de un archivo
    def createMD5Checksum(self, fileParam):
        return hashlib.md5(open(fileParam,'rb').read()).hexdigest()
#obtiene una lista de Archivos y directorios
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
#Obtiene el home path de Bridge
    def getHomeBridgePath(self):
        return str(Path.home()) + os.path.sep + "Bridge"

#el server usara este metodo
    def sendAFile(self, pathParam):
        try:
            with pysftp.Connection(self.host, username=self.usrName, password=self.passw) as sftp:
                with sftp.cd(self.remoteHomeUnix):
                    sftp.put(pathParam)
        finally:
            sftp.close()