class SettersGetterIndex:
    def __init__(self, interpIndex = 0):
        self.interpolationIndex = interpIndex
        # self.interpolationRange = interpRange


    # def setInterpolationIndex(self, interpolation : int) -> int:
    #     self.interpolationIndex = interpolation

    def getInterpolationIndex(self) -> int:
        return self.interpolationIndex

class SettersGetterRange:
    def __init__(self, interpRange=0):
        self.interpolationRange = interpRange

    # def setInterpolationRange(self, interpolationRange : int) -> int:
    #     self.getInterpolationRange = interpolationRange

    def getInterpolationRange(self):
        return self.interpolationRange


class SettersGetterIteration:
    def __init__(self, iterationCount):
        self.iteration = iterationCount
    

    def setIteration(self, iteration : int ) -> int:
        self.interation = iteration
    
    def getIteration(self) -> int:
        return self.interation