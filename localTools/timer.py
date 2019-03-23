import time

class Timer:  
    def __init__(self):
        self.start = 0
        self.end = 0

    def startTimer(self):
        self.start = time.clock()

    def endTimer(self):
        self.end = time.clock()
        return (self.end - self.start)*1000