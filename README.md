# FeatureFlow-App

This Project is based on [FeatureFlow](https://github.com/CM-BF/FeatureFlow) and have been ported to Windows 10. This port inlcudes a user interface which makes it easier to use rather than using command-line.

As of right now, it currently supports videos with a resolution of 640x360 and 1280x720. However as for video with the resolution of 1280x720, this application will automatically split the video into 4 sections and stitch it back all together after each sections has been interpolated.

## To Do List

- [ ] Allow for videos that are 1920x1080
- [ ] Implement proSr or TecoGan
- [ ] Use pyscenedectect for scence changes. This will prevent the application from interpolating between scene changes

## Git Command to pull submodule

```bash
git submodule update --recursive --remote
```

## PreReq for Building File !!(WARNING: If when building, dont use conda to install packages. Use pip for torchvision and pytorch)

```bash
conda create -n open-mmlab python=3.7 -y
conda activate open-mmlab
conda install cudatoolkit=10.0 -c pytorch -y
pip install https://download.pytorch.org/whl/cu100/torchvision-0.3.0-cp37-cp37m-win_amd64.whl #pytorch 1.1.0
pip install torchvision==0.2.2.post3
conda install -c groakat x264 ffmpeg=4.0.2 -c conda-forge -y
cd mmdetection
git checkout tags/v1.0rc1
pip install -r requirements.txt     # windows use pycocotools-windows
pip install mmcv
pip install -v -e .  # or "python setup.py develop"
pip install scikit-image visdom tqdm prefetch-generator wxPython


```

## BUILD

```bash
pyinstaller feflow_ui.py --distpath D:\Programming\Python\FeatureFlow-Build -n FeatureFlow-App -y --clean --add-data .\checkpoints\FeFlow.ckpt;.\checkpoints\ --add-data .\final-model\bdcn_pretrained_on_bsds500.pth;.\final-model\ --add-data .\formbuilder\noname.xrc;.\formbuilder\ --add-binary ffmpeg.exe;.
```
