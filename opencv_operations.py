import cv2

class FrameRate:
    def getInitialFPS(videoName) -> float:
        videoCap = cv2.VideoCapture(videoName)
        fps: float = videoCap.get(cv2.CAP_PROP_FPS)
        return float(fps)
        
class CheckResolution:
    def __init__(self, file_name):
        self.file = file_name
        self.vcap = cv2.VideoCapture(self.file)

    def getWidth(self):
        width = self.vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
        return int(width)

    def getHeight(self):
        height = self.vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return int(height)