import os
import shutil
import time
from pathlib import Path
from featureflow_runner import FeatureFlowRunner as FFR

ffmpeg_exe = Path().cwd() / 'ffmpeg.exe'

class VideoDecimation:
    def __init__(self, input_path_from_gui: str, output_path_from_gui: str):
        self. current_working_dir: str = Path.cwd()
        self.input_video: str = input_path_from_gui
        self.output_path: str = output_path_from_gui

    def removeDuplicateFrames(self):
        filename = self.dir_name_based_off_filename
        file = self.path_to_dir_name_based_off_filename / filename
        print(file)
        print('ffmpeg.exe  -qscale 0 -i ' + str(self.file_name) +
              '.mp4 -vsync 0 -frame_pts true -vf mpdecimate ' + str(self.input_dir / filename) + '-decimated.mp4')
        os.system('ffmpeg.exe -i ' + str(file) + '.mp4 -vsync 0 -frame_pts true -vf mpdecimate ' +
                  str(self.input_dir / filename) + '-decimated.mp4')
        os.system(str(ffmpeg_exe) + ' -i ' + str(file) + '.mp4 -vsync 0 -frame_pts true -vf mpdecimate ' +
                  str(self.input_dir / filename) + '-decimated.mp4')


class Resolution360p:
    def __init__(self, file_input_path_from_gui: str, interpolation: int, output_path_from_gui: str, interpIndex, interpRange):
        self.current_working_dir: str = Path.cwd()
        self.input_video: str = file_input_path_from_gui
        self.video_name: str = os.path.splitext(os.path.basename(file_input_path_from_gui))[0]   # returns file name from example.mp4 to example
        self.interp_num: int = interpolation
        self.output_path: str = output_path_from_gui

        self.index = interpIndex
        self.range = interpRange

        self.finished_file_name: str = Path.cwd() / str(self.video_name + '-final.mp4')
        self.interp_output_file_name: str = str(Path.cwd() / 'output.mp4')

        self.run = FFR()

    def runFeatureFlow(self):
        print(self.interp_num)
        print('Input Video: ', (self.input_video))

        self.run.Runner(self.interp_num, self.input_video, self.output_path, self.index, self.range)

        print(Path(self.interp_output_file_name) / Path(self.output_path))
        print('CDW: ',Path.cwd())
        print('output_file_name: ',self.interp_output_file_name)

        # time.sleep(3)
        # shutil.move(self.interp_output_file_name, str(Path(self.output_path) /
        #                               '{}-final.mp4'.format(self.video_name)))

    def deleteFiles(self):
        cwd = Path(self.current_working_dir)
        filename = self.dir_name_based_off_filename
        cwd_decimated_file = cwd / str(filename + '-decimated.mp4')
        # decimated_file = str(Path(self.input_dir / filename)) + '-decimated.mp4'
        print(cwd_decimated_file)
        os.remove(cwd_decimated_file)


class Resolution720p:
    def __init__(self, file_input_path_from_gui: str, interpolation: int, output_path_from_gui: str, interpIndex, interpRange):
        self.current_working_dir: str = Path.cwd()
        self.input_video: str = file_input_path_from_gui
        self.video_name: str = os.path.splitext(os.path.basename(self.input_video))[
            0]   # returns file name from example.mp4 to example
        self.interp_num: int = interpolation
        self.output_path: str = output_path_from_gui

        self.finished_file_name: str = Path.cwd() / str(self.video_name + '-final.mp4')
        self.interp_output_file_name: str = Path.cwd() / 'output.mp4'

        self.index = interpIndex
        self.range = interpRange

        self.run = FFR()

    def splitVideoIntoSections(self):
        print('Video Name: ', self.video_name)
        input_split_dict = {
            'top-left': [self.input_video, "crop=iw/2:ih/2:0:0", str(Path(self.output_path) / '{}-top-left.mp4').format(self.video_name)],
            'top-right': [self.input_video, "crop=iw/2:ih/2:ow:0", str(Path(self.output_path) / '{}-top-right.mp4').format(self.video_name)],
            'bottom-left': [self.input_video, "crop=iw/2:ih/2:0:oh", str(Path(self.output_path) / '{}-bottom-left.mp4').format(self.video_name)],
            'bottom-right': [self.input_video, "crop=iw/2:ih/2:ow:oh", str(Path(self.output_path) / '{}-bottom-right.mp4').format(self.video_name)],
        }

        for v in input_split_dict.items():
            # print(v[1][0])
            # print(v[1][1])
            print(str(ffmpeg_exe) + ' -i ' +
                  v[1][0] + ' -vsync 0 -frame_pts true -vf '+'"' + v[1][1] + '"' + ' ' + v[1][2])
            os.system(str(ffmpeg_exe) + ' -i ' +
                      v[1][0] + ' -vsync 0 -frame_pts true -vf '+'"' + v[1][1] + '"' + ' ' + v[1][2])

    def runFeatureFlow(self):
        input_split_files = [str(Path(self.output_path) / '{}-top-left.mp4'.format(self.video_name)),
                             str(Path(self.output_path) / '{}-top-right.mp4'.format(self.video_name)),
                             str(Path(self.output_path) / '{}-bottom-left.mp4'.format(self.video_name)),
                             str(Path(self.output_path) / '{}-bottom-right.mp4'.format(self.video_name))
                             ]

        for video in input_split_files:
            print(video)
            self.run.Runner(self.interp_num, video, str(Path(self.output_path)), self.index, self.range)
            shutil.move('output.mp4', video)

    def stitchVideo(self):
        input_split_files = [str(Path(self.output_path) / '{}-top-left.mp4'.format(self.video_name)),
                             str(Path(self.output_path) / '{}-top-right.mp4'.format(self.video_name)),
                             str(Path(self.output_path) / '{}-bottom-left.mp4'.format(self.video_name)),
                             str(Path(self.output_path) / '{}-bottom-right.mp4'.format(self.video_name))
                             ]
        os.system(str(ffmpeg_exe) +
                  ' -i ' + input_split_files[0] +
                  ' -i ' + input_split_files[1] +
                  ' -i ' + input_split_files[2] +
                  ' -i ' + input_split_files[3] +
                  ' -filter_complex "[0:v][1:v]hstack=inputs=2[top];[2:v][3:v]hstack=inputs=2[bottom];[top][bottom]vstack=inputs=2[v]" -map "[v]" ' +
                  str(Path(self.output_path) / '{}-final.mp4'.format(self.video_name)))
        for video in input_split_files:
            os.remove(video)
