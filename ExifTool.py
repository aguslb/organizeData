import subprocess
import os
import json
import sys

class ExifTool(object):

    sentinel = ""
    executable = ""
    def __init__(self):
        if sys.platform.startswith('win32'):
            self.sentinel = "{ready}\r\n"
            self.executable = "C:\\WINDOWS\\exiftool.exe"
        else :
            self.sentinel = "{ready}\n"
            self.executable = "/usr/local/bin/exiftool"

    def enter(self):
        self.process = subprocess.Popen(
         [self.executable, "-stay_open", "True",  "-@", "-"],
         universal_newlines=True,
         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def  exit(self):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.sentinel):
            output += os.read(fd, 4096).decode('utf-8')
        return output[:-len(self.sentinel)]

    def get_metadata(self, *filenames):
        self.enter()
        jsonRet = json.loads(self.execute("-G", "-j", "-n", *filenames))
        self.exit()
        return jsonRet