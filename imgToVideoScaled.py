import json
import os
from pathlib import Path
from collections import namedtuple
from json import JSONEncoder
ffmpeg_exe = Path.cwd() / 'ffmpeg.exe'

class ImgToVid:

    def run(self, interpolatedFramesPath : str, fileName : str):
        self.dataFromJson = None
        self.newFps = None
        self.videoName = None
        self.data = None
        self.jsonFps = None
        print('OUT: ',Path(interpolatedFramesPath).parent.parent)
        with open(str((Path(interpolatedFramesPath).parent.parent) / 'interp_data.json')) as json_file:
            self.data = json.load(json_file)

        pairs = self.data.items()
        dataFromJson = []

        for key, value in pairs:
            dataFromJson.append(value)
        print(dataFromJson[0])
        self.videoName = dataFromJson[0]
        self.newFps = dataFromJson[1]
        print( str(ffmpeg_exe) + " -framerate " + str(self.newFps) + " -i " + str(interpolatedFramesPath) + '\\%10d.png' + ' -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p ' + (str(Path(interpolatedFramesPath).parent / str(self.videoName)) + '_result.mp4'))
        os.system( str(ffmpeg_exe) + " -framerate " + str(self.newFps) + " -i " + str(interpolatedFramesPath) + '\\%10d.png' + ' -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p ' + (str(Path(interpolatedFramesPath).parent / str(self.videoName)) + '_result.mp4'))

# if __name__ == "__main__":
#     itv = ImgToVid()
#     itv.run('C:\\Users\\LoopyELBARTO\\Downloads\\Test\\Bomb\\Out', 'bomb.mp4')