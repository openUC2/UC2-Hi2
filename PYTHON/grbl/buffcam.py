import cv2, queue, threading, time

# https://stackoverflow.com/questions/33432426/importerror-no-module-named-queue
# bufferless VideoCapture
class VideoCapture:
    def __init__(self, name):
        self.cap = cv2.VideoCapture(name, cv2.CAP_GSTREAMER)
        #self.cap.set(cv2.CAP_PROP_CONVERT_RGB, False);
        self.q = queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()
        self._isopen = True
        
    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        self._isopen = True
        while True:
            ret, frame = self.cap.read()
            if not ret:
                self._isopen = False
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except Queue.Empty:
                    pass
            self.q.put(frame)
    
    def isOpened(self):
        return self._isopen

    def release(self):
        self.cap.release()

    def read(self):
        return None, self.q.get()
