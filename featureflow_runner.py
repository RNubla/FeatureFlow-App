# SeDraw
from ThirdParty.FeatureFlow.feature_flow_interface import ffmpeg_exe
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
# from ThirdParty.FeatureFlow.models.bdcn import bdcn as bdcn
from ThirdParty.FeatureFlow.models.bdcn import bdcn
# from feflow_ui import IndexPro
import shutil
ffmpeg_exe = Path.cwd() / 'ffmpeg.exe'

class FeatureFlowRunner:
    def __init__(self):
        # self.cuda_enabled = cuda
        # add cpu mode
        # self.ffmpeg_exe = str(Path(__file__).resolve() / 'ffmpeg.exe')
        self.iteration : int
        self.interpolationIndex : int 
        self.interpolationRange : int 
        self.dir_path : str = ''
        self.imgt = None
        
        self.bdcn = bdcn.BDCN()
        self.bdcn.cuda()
        self.structure_gen = layers.StructureGen(3)
        self.structure_gen.cuda()
        self.detail_enhance = layers.DetailEnhance()
        self.detail_enhance.cuda()

        # # Channel wise mean calculated on adobe240-fps training dataset
        self.mean = [0.5, 0.5, 0.5]
        self.std = [0.5, 0.5, 0.5]
        self.normalize = transforms.Normalize(mean=self.mean, std=self.std)
        self.transform = transforms.Compose([transforms.ToTensor(), self.normalize])

        self.negmean = [-1 for x in self.mean]
        self.restd = [2, 2, 2]
        self.revNormalize = transforms.Normalize(mean=self.negmean, std=self.restd)
        self.TP = transforms.Compose([self.revNormalize, transforms.ToPILImage()])

    def _pil_loader(self, path, cropArea=None, resizeDim=None, frameFlip=0):
        # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
        with open(path, 'rb') as f:
            self.img = Image.open(f)
            # Resize image if specified.
            self.resized_img = self.img.resize(resizeDim, Image.ANTIALIAS) if (resizeDim != None) else self.img
            # Crop image if crop area specified.
            self.cropped_img = self.img.crop(cropArea) if (cropArea != None) else self.resized_img
            # Flip image horizontally if specified.
            self.flipped_img = self.cropped_img.transpose(Image.FLIP_LEFT_RIGHT) if frameFlip else self.cropped_img
            return self.flipped_img.convert('RGB')

    def ToImage(self, frame0, frame1):
        with torch.no_grad():
            self.img0 = frame0.cuda()
            self.img1 = frame1.cuda()

            self.img0_e = torch.cat([self.img0, torch.tanh(self.bdcn(self.img0)[0])], dim=1)
            self.img1_e = torch.cat([self.img1, torch.tanh(self.bdcn(self.img1)[0])], dim=1)

            self.ref_imgt, _ = self.structure_gen((self.img0_e, self.img1_e))
            self.imgt = self.detail_enhance((self.img0, self.img1, self.ref_imgt))
            self.imgt = torch.clamp(self.imgt, max=1., min=-1.)
        return self.imgt

    def IndexHelper(self,i, digit):
        index = str(i)
        for j in range(digit-len(str(i))):
            index = '0' + index
        return index
    
    def VideoToSequence(self, path, time):
        video = cv2.VideoCapture(path)
        self.dir_path = 'frames_tmp'
        if(Path(self.dir_path).exists()):
            shutil.rmtree(self.dir_path)
        os.mkdir(self.dir_path)
        self.fps = int(video.get(cv2.CAP_PROP_FPS))
        length = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        print('making ' + str(length) + ' frame sequence in ' + self.dir_path)
        i = -1
        while(True):
            (grabbed, frame) = video.read()
            if not grabbed:
                break
            i+=1
            index = self.IndexHelper(i*time, len(str(time*length)))
            leading_zeroes = str(index).zfill(10)
            cv2.imwrite(self.dir_path + '/' + leading_zeroes + '.png', frame)
        return [self.dir_path, length, self.fps]

    def Runner(self, interp : int, input_file : str, output_path: str, interpIndex, interpRange):

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
        self.dict1 = torch.load(checkpoint_file)
        self.structure_gen.load_state_dict(self.dict1['state_dictGEN'], strict=False)
        self.detail_enhance.load_state_dict(self.dict1['state_dictDE'], strict=False)

        self.bdcn.eval()
        self.structure_gen.eval()
        self.detail_enhance.eval()

        IE = 0
        PSNR = 0
        count = 0
            
        [self.dir_path, self.frame_count, self.fps] = self.VideoToSequence(input_file, interp)
        for i in range(iter):
            print('processing iter' + str(i+1) + ', ' + str((i+1)*self.frame_count) + ' frames in total')
            # print('Iteration: ',iter)
            # iteration = SettersGetterIteration(iter)
            filenames = os.listdir(self.dir_path)
            filenames.sort()
            interpRange.interpolationRange = (len(filenames) - 1)
            print(interpRange.getInterpolationRange())
            for i in tqdm(range(0, interpRange.getInterpolationRange())):
                interpIndex.interpolationIndex = i
                self.first_arguements = os.path.join(self.dir_path, filenames[i])
                self.second_arguements = os.path.join(self.dir_path, filenames[i+1])
                index1 = int(re.sub('\D', '', filenames[i]))
                index2 = int(re.sub('\D', '', filenames[i+1]))
                index = int((index1 + index2) /2)
                self.out_arguement = os.path.join(self.dir_path, self.IndexHelper(index, len(str(interp * self.frame_count).zfill(10))) + ".png")

                x0 = self.transform(self._pil_loader(self.first_arguements)).unsqueeze(0)
                x1 = self.transform(self._pil_loader(self.second_arguements)).unsqueeze(0)

                assert (x0.size(2) == x1.size(2))
                assert (x0.size(3) == x1.size(3))

                intWidth = x0.size(3)
                intHeight = x0.size(2)
                channel = x0.size(1)
                if not channel == 3:
                    print('Not RGB image')
                    continue
                count += 1

                self.first, self.second = x0, x1
                self.imgt = self.ToImage(self.first, self.second)

                self.imgt_np = self.imgt.squeeze(0).cpu().numpy()
                self.imgt_png = np.uint8(((self.imgt_np + 1.0) / 2.0).transpose(1, 2, 0)[:, :, ::-1] * 255)
                cv2.imwrite(self.out_arguement, self.imgt_png)
        print('CWD FROM RUNNER: ', Path.cwd())
        print(str(ffmpeg_exe) + " -framerate " + str(interp*self.fps) + " -i " + str(Path(output_path).parent) + '\\' + self.dir_path + '\\%10d.png' + ' -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p output.mp4')
        os.system( str(ffmpeg_exe) + " -framerate " + str(interp*self.fps) + " -i " + str(Path(output_path).parent) + '\\' + self.dir_path + '\\%10d.png' + ' -c:v libx264 -profile:v high -crf 20 -pix_fmt yuv420p output.mp4')
        shutil.rmtree(self.dir_path)
        torch.cuda.empty_cache()