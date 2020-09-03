# SeDraw
from os.path import dirname
from pathlib import Path
import re
import argparse
import os
import torch
import cv2
import torchvision.transforms as transforms
from PIL import Image
from ThirdParty.FeatureFlow.src import pure_network as layers
from tqdm import tqdm
import numpy as np
import math
from ThirdParty.FeatureFlow.models.bdcn import bdcn as bdcn
import shutil


class FeatureFlowRunner:
    def __init__(self):
        # self.cuda_enabled = cuda
        # add cpu mode
        self.ffmpeg_exe = Path().cwd() / 'bin/ffmpeg.exe'
        self.iteration : int
        self.interpolationIndex : int
        self.interpolationRange : int
        
        self.bdcn = bdcn.BDCN()
        self.bdcn.cuda()
        self.structure_gen = layers.StructureGen(3)
        self.structure_gen.cuda()
        self.detail_enhance = layers.DetailEnhance()
        self.detail_enhance.cuda()

        # # Channel wise mean calculated on adobe240-fps training dataset
        self.mean = [0.5, 0.5, 0.5]
        self.std = [0.5, 0.5, 0.5]
        self.normalize = transforms.Normalize(mean=self.mean,
                                         std=self.std)
        self.transform = transforms.Compose([transforms.ToTensor(), self.normalize])

        self.negmean = [-1 for x in self.mean]
        self.restd = [2, 2, 2]
        self.revNormalize = transforms.Normalize(mean=self.negmean, std=self.restd)
        self.TP = transforms.Compose([self.revNormalize, transforms.ToPILImage()])

    def ToImage(self, frame0, frame1):
        with torch.no_grad():
            img0 = frame0.cuda()
            img1 = frame1.cuda()

            img0_e = torch.cat([img0, torch.tanh(bdcn(img0)[0])], dim=1)
            img1_e = torch.cat([img1, torch.tanh(bdcn(img1)[0])], dim=1)

            ref_imgt, _ = self.structure_gen((img0_e, img1_e))
            imgt = self.detail_enhance((img0, img1, ref_imgt))
            imgt = torch.clamp(imgt, max=1., min=1.)
        return imgt

    def IndexHelper(self,i, digit):
        index = str(i)
        for j in range(digit-len(str(i))):
            index = '0' + index
        return index
    
    def VideoToSequence(self, path, time):
        video = cv2.VideoCapture(path)
        dir_path = 'frames_tmp'
        os.mkdir(dir_path)
        fps = int(video.get(cv2.CAP_PROP_FPS))
        length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        print('making ' + str(length) + ' frame sequence in ' + dirname)
        i = -1
        while(True):
            (grabbed, frame) = video.read()
            if not grabbed:
                break
            i+=1
            index = self.IndexHelper(i*time, len(str(time*length)))
            leading_zeroes = str(index).zfill(10)
            cv2.imwrite(dir_path + '/' + leading_zeroes + '.png', frame)
        return [dir_path, length, fps]

    def setIteration(self, iteration : int ) -> int:
        self.interation = iteration

    def setInterpolationIndex(self, interpolation : int) -> int:
        self.interpolationIndex = interpolation

    def setInterpolationRange(self, interpolationRange : int) -> int:
        self.getInterpolationRange = interpolationRange


    def getIteration(self) -> int:
        return self.interation

    def getInterpolationIndex(self) -> int:
        return self.interpolationIndex

    def getInterpolationRange(self):
        return self.interpolationRange

    def Runner(self, interp : int, input_file : str):
        cwd = Path(__file__).resolve()
        print('CWD: ',cwd.parent)
        model_file = cwd.parent / 'final-model/bdcn_pretrained_on_bsds500.pth'
        checkpoint_file = cwd.parent / 'checkpoints/FeFlow.ckpt'
        print(model_file)
        print(model_file.exists())
        print('INTERP: ',interp)
        iter = math.log(interp, int(2))
        if iter%1:
            print('the times of interpolating must be power of 2!!')
            return
        iter = int(iter)
        self.bdcn.load_state_dict(torch.load(model_file))
        dict1 = torch.load(checkpoint_file)
        self.structure_gen.load_state_dict(dict1['state_dictGEN'], strict=False)
        self.detail_enhance.load_state_dict(dict1['state_dictDE'], strict=False)

        self.bdcn.eval()
        self.structure_gen.eval()
        self.detail_enhance.eval()

        IE = 0
        PSNR = 0
        count = 0
            
        [dir_path, frame_count, fps] = self.VideoToSequence(input_file, interp)

        for i in range(iter):
            print('processing iter' + str(i+1) + ', ' + str((i+1)*frame_count) + ' frames in total')
            # print('Iteration: ',iter)
            self.setIteration(iter)
            filenames = os.listdir(dir_path)
            filenames.sort()
            self.setInterpolationRange(len(filenames) - 1)
            for i in tqdm(range(0, self.getInterpolationRange())):
                self.setInterpolationIndex(i)
                first_arguements = os.path.join(dir_path, filenames[i])
                second_arguements = os.path.join(dir_path, filenames[i+1])
                index1 = int(re.sub('\D', '', filenames[i]))
                index2 = int(re.sub('\D', '', filenames[i+1]))
                index = int((index1 + index2) /2)
                out_arguement = os.path.join(dir_path, self.IndexHelper(index, len(str(self.))))

# ffmpeg_exe = Path().cwd() / 'bin/ffmpeg.exe'

# def _pil_loader(path, cropArea=None, resizeDim=None, frameFlip=0):


#     # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
#     with open(path, 'rb') as f:
#         img = Image.open(f)
#         # Resize image if specified.
#         resized_img = img.resize(resizeDim, Image.ANTIALIAS) if (resizeDim != None) else img
#         # Crop image if crop area specified.
#         cropped_img = img.crop(cropArea) if (cropArea != None) else resized_img
#         # Flip image horizontally if specified.
#         flipped_img = cropped_img.transpose(Image.FLIP_LEFT_RIGHT) if frameFlip else cropped_img
#         return flipped_img.convert('RGB')



# bdcn = bdcn.BDCN()
# bdcn.cuda()
# structure_gen = layers.StructureGen(3)
# structure_gen.cuda()
# detail_enhance = layers.DetailEnhance()
# detail_enhance.cuda()


# # Channel wise mean calculated on adobe240-fps training dataset
# mean = [0.5, 0.5, 0.5]
# std = [0.5, 0.5, 0.5]
# normalize = transforms.Normalize(mean=mean,
#                                  std=std)
# transform = transforms.Compose([transforms.ToTensor(), normalize])

# negmean = [-1 for x in mean]
# restd = [2, 2, 2]
# revNormalize = transforms.Normalize(mean=negmean, std=restd)
# TP = transforms.Compose([revNormalize, transforms.ToPILImage()])


# def ToImage(frame0, frame1):

#     with torch.no_grad():

#         img0 = frame0.cuda()
#         img1 = frame1.cuda()

#         img0_e = torch.cat([img0, torch.tanh(bdcn(img0)[0])], dim=1)
#         img1_e = torch.cat([img1, torch.tanh(bdcn(img1)[0])], dim=1)
#         ref_imgt, _ = structure_gen((img0_e, img1_e))
#         imgt = detail_enhance((img0, img1, ref_imgt))
#         imgt = torch.clamp(imgt, max=1., min=-1.)

#     return imgt
# def IndexHelper(i, digit):
#     index = str(i)
#     for j in range(digit-len(str(i))):
#         index = '0'+index
#     return index

# def VideoToSequence(path, time):
#     video = cv2.VideoCapture(path)
#     dir_path = 'frames_tmp'
#     # os.system("rm -rf %s" % dir_path)
#     # shutil.rmtree(dir_path)
#     os.mkdir(dir_path)
#     fps = int(video.get(cv2.CAP_PROP_FPS))
#     length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     print('making ' + str(length) + ' frame sequence in ' + dir_path)
#     i = -1
#     while (True):
#         (grabbed, frame) = video.read()
#         if not grabbed:
#             break
#         i = i + 1
#         index = IndexHelper(i*time, len(str(time*length)))
#         # cv2.imwrite(dir_path + '/' + index + '.png', frame)
#         leading_zeroes = str(index).zfill(10)
#         cv2.imwrite(dir_path + '/' + leading_zeroes + '.png', frame)
#         # print(index)
#     return [dir_path, length, fps]

# iter : int = 0
# filenames : str = None
# interpoIndex : int = 0
# # interpoRange : int = len(filenames) -1
# interpoRange : int = 0



# def setIteration(iteration : int ) -> int:
#     global iter
#     iter = iteration

# def setInterpolationIndex(interpolation : int) -> int:
#     global interpoIndex
#     interpoIndex = interpolation

# def setInterpolationRange(interpolationRange : int) -> int:
#     global interpoRange
#     interpoRange = interpolationRange


# def getIteration() -> int:
#     return iter

# def getInterpolationIndex() -> int:
#     return interpoIndex

# def getInterpolationRange():
#     return interpoRange

# def main(interp : int, input_file : str):
#     cwd = Path(__file__).resolve()
#     print('CWD: ',cwd.parent)
#     model_file = cwd.parent / 'final-model/bdcn_pretrained_on_bsds500.pth'
#     checkpoint_file = cwd.parent / 'checkpoints/FeFlow.ckpt'
#     print(model_file)
#     print(model_file.exists())
#     print('INTERP: ',interp)
#     # initial
#     # iter = math.log(args.t_interp, int(2))
#     iter = math.log(interp, int(2))
#     if iter%1:
#         print('the times of interpolating must be power of 2!!')
#         return
#     iter = int(iter)
#     # bdcn.load_state_dict(torch.load('%s' % (args.bdcn_model)))
#     # bdcn.load_state_dict(torch.load('%s' % (model)))
#     bdcn.load_state_dict(torch.load(model_file))
#     # dict1 = torch.load(args.checkpoint)
#     dict1 = torch.load(checkpoint_file)
#     structure_gen.load_state_dict(dict1['state_dictGEN'], strict=False)
#     detail_enhance.load_state_dict(dict1['state_dictDE'], strict=False)

#     bdcn.eval()
#     structure_gen.eval()
#     detail_enhance.eval()

#     IE = 0
#     PSNR = 0
#     count = 0
#     # [dir_path, frame_count, fps] = VideoToSequence(args.video_path, args.t_interp)
#     [dir_path, frame_count, fps] = VideoToSequence(input_file, interp)

#     for i in range(iter):
#         print('processing iter' + str(i+1) + ', ' + str((i+1)*frame_count) + ' frames in total')
#         # print('Iteration: ',iter)
#         setIteration(iter)
#         filenames = os.listdir(dir_path)
#         filenames.sort()
#         # for i in tqdm(range(0, len(filenames) - 1)):
#         # print('Filename: ', filenames)
#         # interpoRange : int = len(filenames) - 1
#         setInterpolationRange(len(filenames) -1)
#         # print('InterpoRange: ', interpoRange)
#         for i in tqdm(range(0, getInterpolationRange())):
#             # global interpoIndex
#             # interpoIndex = i
#             setInterpolationIndex(i)
#             # progressBar(getInterpolationIndex())
#             # print('InterpoIndex: ', interpoIndex)
#             arguments_strFirst = os.path.join(dir_path, filenames[i])
#             arguments_strSecond = os.path.join(dir_path, filenames[i + 1])
#             index1 = int(re.sub("\D", "", filenames[i]))
#             index2 = int(re.sub("\D", "", filenames[i + 1]))
#             index = int((index1 + index2) / 2)
#             arguments_strOut = os.path.join(dir_path,
#                                             # IndexHelper(index, len(str(args.t_interp * frame_count).zfill(10))) + ".png")
#                                             IndexHelper(index, len(str(interp * frame_count).zfill(10))) + ".png")

#             # print(arguments_strFirst)
#             # print(arguments_strSecond)
#             # print(arguments_strOut)

#             X0 = transform(_pil_loader(arguments_strFirst)).unsqueeze(0)
#             X1 = transform(_pil_loader(arguments_strSecond)).unsqueeze(0)

#             assert (X0.size(2) == X1.size(2))
#             assert (X0.size(3) == X1.size(3))

#             intWidth = X0.size(3)
#             intHeight = X0.size(2)
#             channel = X0.size(1)
#             if not channel == 3:
#                 print('Not RGB image')
#                 continue
#             count += 1

#             first, second = X0, X1
#             imgt = ToImage(first, second)

#             imgt_np = imgt.squeeze(
#                 0).cpu().numpy()  # [:, intPaddingTop:intPaddingTop+intHeight, intPaddingLeft: intPaddingLeft+intWidth]
#             imgt_png = np.uint8(((imgt_np + 1.0) / 2.0).transpose(1, 2, 0)[:, :, ::-1] * 255)
#             cv2.imwrite(arguments_strOut, imgt_png)

#     # os.system("ffmpeg -framerate " + str(output_fps) + " -pattern_type glob -i '" + dir_path + "/*.png' -pix_fmt yuv420p output.mp4")
#     # os.system("ffmpeg -f image2 -framerate " + str(interp*fps) + " -i .\\" + dir_path + "\\%010d.png -pix_fmt yuv420p output.mp4")
#     # os.system(str(ffmpeg_exe) + " -f image2 -framerate " + str(interp*fps) + " -i .\\" + dir_path + "\\%010d.png -pix_fmt yuv420p output.mp4")
#     # os.system(str(ffmpeg_exe) + " -f image2 -framerate " + str(interp*fps) + " -i .\\" + dir_path + "\\%010d.png -vcodec libx264 -profile:v high444 -refs 16 -crf 0 -preset ultrafast output.mp4")
#     os.system(str(ffmpeg_exe) + " -f image2 -framerate " + str(interp*fps) + " -i .\\" + dir_path + "\\%010d.png -pix_fmt yuv420p output.mp4")
#     # os.system("ffmpeg -f image2 -i .\\" + dir_path + "\\%010d.png -pix_fmt yuv420p output.mp4")
#     # os.system("rm -rf %s" % dir_path)
#     shutil.rmtree(dir_path)
#     torch.cuda.empty_cache()


# main()


