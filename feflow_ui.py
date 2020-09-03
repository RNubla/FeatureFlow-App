import wx
from wx import xrc
import wx.adv
from pathlib import Path
import threading

from feature_flow_interface import CheckResolution, Resolution720p, Resolution360p, InformationGetters, FrameRate


class FeFlowApp(wx.App):
    def OnInit(self):
        self.xrcFile: str = str(Path.cwd() / 'formbuilder' / 'noname.xrc')
        self.res = xrc.XmlResource(self.xrcFile)
        self.init_frame()
        return True

    def init_frame(self):
        self.interpNum: int = 2
        self.inputFile: str = ''
        self.outputPath: str = ''
        self.FPS: float = 0.0
        self.newFPS: float = 0.0
        self.condition = threading.Condition()

        self.mainFrame = self.res.LoadFrame(None, 'mainFrame')
        self.mainMenuBar = xrc.XRCCTRL(self.mainFrame, 'mainMenuBar')

        self.quitFromMenuBar = xrc.XRCCTRL(self.mainFrame, 'exitMenuItem')
        self.mainFrame.Bind(wx.EVT_MENU, self.onQuit,
                            id=xrc.XRCID('exitMenuItem'))

        self.ogFPS = xrc.XRCCTRL(self.mainFrame, 'ogFPSTextCtrl')
        self.mainFrame.Bind(wx.EVT_BUTTON, self.onSelectFile,
                            id=xrc.XRCID('ogFPSTextCtrl'))

        self.interpFPS = xrc.XRCCTRL(self.mainFrame, 'interpFPSTextCtrl')
        self.mainFrame.Bind(wx.EVT_CHOICE, self.getChoice,
                            id=xrc.XRCID('interpFPSTextCtrl'))

        self.choice = xrc.XRCCTRL(self.mainFrame, 'interpolationChoice')
        self.mainFrame.Bind(wx.EVT_CHOICE, self.getChoice,
                            id=xrc.XRCID('interpolationChoice'))

        self.videoPicker = xrc.XRCCTRL(self.mainFrame, 'videoFilePicker')
        self.mainFrame.Bind(wx.EVT_FILEPICKER_CHANGED,
                            self.onSelectFile, id=xrc.XRCID('videoFilePicker'))

        self.outputPicker = xrc.XRCCTRL(self.mainFrame, 'outputDirPicker')
        self.mainFrame.Bind(wx.EVT_DIRPICKER_CHANGED,
                            self.onSelectOutputDir, id=xrc.XRCID('outputDirPicker'))

        self.runBtn = xrc.XRCCTRL(self.mainFrame, 'RunBtn')
        self.mainFrame.Bind(
            wx.EVT_BUTTON, self.applicationThreads, id=xrc.XRCID('RunBtn'))

        # self.inProgressDialog = xrc.XRCCTRL(self.mainFrame, 'progressDialog')
        # self.mainFrame.Bind(wx.EVT_BUTTON, self.showProgressBar, id=xrc.XRCID('progressDialog'))

        self.statusBar = xrc.XRCCTRL(self.mainFrame, 'statusBar')
        self.mainFrame.Bind(
            wx.EVT_TEXT, self.showIterationCount, id=xrc.XRCID('statusBar'))

        self.pbar = xrc.XRCCTRL(self.mainFrame, 'progressBar')
        # self.mainFrame.Bind(wx.EVT_BUTTON, self.applicationThreads, id=xrc.XRCID('progressBar'))
        self.mainFrame.Bind(
            wx.EVT_BUTTON, self.applicationThreads, id=xrc.XRCID('progressBar'))

        self.mainFrame.Show()

    def onQuit(self, event):
        self.mainFrame.Close()

    def getChoice(self, event):
        choice = self.choice.GetStringSelection()
        self.choice.GetCurrentSelection()
        if choice == '2x':
            self.interpFPS.SetValue('')
            print('Interpolation Number: ', choice)
            self.interpNum = 2
            self.newFPS = float(self.FPS * self.interpNum)
            self.interpFPS.write(str(self.newFPS))
        elif choice == '4x':
            self.interpFPS.SetValue('')
            print('Interpolation Number: ', choice)
            self.interpNum = 4
            self.newFPS = float(self.FPS * self.interpNum)
            self.interpFPS.write(str(self.newFPS))
        elif choice == '8x':
            self.interpFPS.SetValue('')
            print('Interpolation Number: ', choice)
            self.interpNum = 8
            self.newFPS = float(self.FPS * self.interpNum)
            self.interpFPS.write(str(self.newFPS))
        # print(self.interpNum)

    def onSelectFile(self, event):
        file = self.videoPicker.GetPath()
        self.inputFile = file

        fps = FrameRate.getInitialFPS(self.inputFile)
        self.FPS = fps
        self.ogFPS.SetValue(str(self.FPS))
        print('INPUT FILE : ', self.inputFile)

    def onSelectOutputDir(self, event):
        path = self.outputPicker.GetPath()
        self.outputPath = path
        print('Output Folder: ', self.outputPath)

    def completeDialog(self):
        wx.MessageBox('Feature Flow has finished interpolating your video. \n Please check your output directory',
                      'Interpolation Complete', wx.OK | wx.ICON_EXCLAMATION)

    def missingFileDialog(self):
        wx.MessageBox('You have not selected an Input Video or and Output Directory. \n Please specify them',
                      'Error', wx.OK | wx.ICON_ERROR)

    def onRunFeatureFlow(self, event):
        # index = InformationGetters.interpolationIndex()
        # range = InformationGetters.interpolationRange()
        # print(range)
        if self.inputFile != '' and self.outputPath != '':
            resolution = CheckResolution(self.inputFile)
            if resolution.getWidth() < int(1280) and resolution.getHeight() < int(720):
                interpolate360 = Resolution360p(
                    self.inputFile, self.interpNum, self.outputPath)
                interpolate360.runFeatureFlow()
                self.completeDialog()
            else:
                interpolate720 = Resolution720p(
                    self.inputFile, self.interpNum, self.outputPath)
                interpolate720.splitVideoIntoSections()
                interpolate720.runFeatureFlow()
                interpolate720.stitchVideo()
                self.completeDialog
        else:
            self.missingFileDialog()

    def showProgressBar(self, cond):
        print('Starting showProgressBar Thread')
        t = threading.currentThread()
        with cond:
            cond.wait()
            print('Resource is availabe to showProgressBar')
            self.pbar.SetRange(InformationGetters.interpolationRange())
            self.pbar.SetValue(InformationGetters.interpolationIndex())
            print('Range: ', InformationGetters.interpolationRange())
            # wx.ProgressDialog('Interpolation In Progress', 'Interpolating your video', maximum=100)

    def fflowProducer(self, cond):
        print('Starting Feature Flow Producer Thread')
        with cond:
            print('Making resource availale for showProgressBar')
            # self.onRunFeatureFlow
            cond.notifyAll()

        # print('Range: ', InformationGetters.interpolationRange())
        # print('Index: ', InformationGetters.interpolationIndex())
        # progressDialog = wx.ProgressDialog('Interpolation In Progress', 'Interpolating your video', maximum=InformationGetters.interpolationRange)
        # progressDialog.Update(InformationGetters.interpolationIndex)

    def applicationThreads(self, event):
        # pbar = threading.Thread(name='Progress Bar', target=self.showProgressBar, args=(self.condition,))
        # fflow = threading.Thread(name='FeatureFlow Producer', target=self.onRunFeatureFlow, args=(self.condition,))
        # pbar.start()
        # fflow.start()
        runFeatureFlow = threading.Thread(
            target=self.onRunFeatureFlow, args=(event,))
        # progressBar = threading.Thread(target=self.showProgressBar, args=(event,))
        runFeatureFlow.start()
        # progressBar.start()
        # progressBar.join()
        # runFeatureFlow.join()

    def showIterationCount(self):
        iteration = InformationGetters.iterationCount()
        self.statusBar.SetStatusText('Iteration: ', str(iteration))


if __name__ == "__main__":
    app = FeFlowApp(False)
    app.MainLoop()
