import os
import pysftp
import hashlib
import tarfile
import datetime
from pathlib import Path


class FileOrganizerClient:

    usrName = "zid_0"
    MD5File = "MD5.check"
    host = "hpz220w.local"
    remoteHomeWin = "H:\\Bridge"
    succesFile = "MD5Result.check"
    privateKey = "/Users/agus/.ssh/id_rsa.fileOrg"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # envia los archivos con SFTP remotamente
    def sendFiles(self, filesParam):
        homepath = self.getHomeBridgePath()
        try:
            with pysftp.Connection(self.host, username=self.usrName, private_key=self.privateKey) as sftp:
                with sftp.cd(self.remoteHomeWin):
                    for activeFile in filesParam:
                        fileTosend = homepath + os.path.sep + activeFile
                        sftp.put(fileTosend, callback=lambda x, y: print(
                            "faltan {} de {}".format(((y-x)/2048),(y/2048))))
        finally:
            sftp.close()

    # Obtiene el home path de Bridge
    def getHomeBridgePath(self):
        return str(Path.home()) + os.path.sep + "Bridge"

    # Genera un MD5 de un archivo
    def createMD5Checksum(self, fileParam):
        return hashlib.md5(open(fileParam, 'rb').read()).hexdigest()

    # obtiene una lista de Archivos y directorios
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

    # revisar los archivos con md5
    def md5CheckFile(self, listFilesParam, extend):
        home = self.getHomeBridgePath()
        homeMD5File = str(home) + str(os.path.sep) + \
            str(self.MD5File) + str(extend)
        if os.path.exists(homeMD5File):
            os.remove(homeMD5File)
        try:
            with open(str(homeMD5File), "a") as fp:
                for i in listFilesParam:
                    activeFile = str(home) + str(os.path.sep) + i
                    fp.write(str(i) + "," +
                             str(self.createMD5Checksum(activeFile))+"\n")
                fp.close()
        finally:
            fp.close()

    # Punto de entrada
    def clientExecute(self):
        print(self.now + " Start")
        homepath = self.getHomeBridgePath()
        resultFilePath = homepath + os.path.sep + self.succesFile
        if os.path.exists(resultFilePath):
            print(self.now + " If file exist")
            try:
                with open(resultFilePath) as fp:
                    for cnt, line in enumerate(fp):
                        print("Line {}: {}".format(cnt, line))
                        rmLineFilePath = homepath + os.path.sep + line
                        if os.path.exists(rmLineFilePath):
                            print(self.now + " Removing files that where organized successfully")
                            os.remove(rmLineFilePath)
            finally:
                fp.close()
                os.remove(resultFilePath)
        listFileDir = self.getListFilesAndDir(homepath)
        for activeDir in listFileDir[1]:
            print(self.now + " Compressing directory")
            pathTGZ = homepath + os.path.sep + activeDir
            with tarfile.open(pathTGZ + ".tgz", "w:gz") as tar:
                for name in os.listdir(pathTGZ):
                    tar.add(pathTGZ + os.path.sep + name)
            listFileDir[0].append(str(activeDir + ".tgz"))
        print(self.now + " Check MD5")
        self.md5CheckFile(listFileDir[0], "")
        print(self.now + " Add all files")
        listFileDir[0].append(self.MD5File)
        print(self.now + " Sending files")
        self.sendFiles(listFileDir[0])
        print(self.now + " End")


fOC = FileOrganizerClient()
fOC.clientExecute()
