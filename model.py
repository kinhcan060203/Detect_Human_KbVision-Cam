from my_utils import check_image_focus
from my_utils import draw_predict, draw_boudary, check_alarm, send_telegram, find_center_points, PolygonDrawer
import json
from shapely.geometry import Point, Polygon
import torch
import cv2
import numpy as np
import time
from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import non_max_suppression

# rtsp://{user}:{password}@{kb-vision-id}:554

conf_thres = 0.4
iou_thres = 0.3
max_det = 10
img_size = (512, 512)

class Model(DetectMultiBackend):

    def __init__(self, streamName,rtsp,delay_thres=5,alarm_thres=15):
        super().__init__(weights="yolov5s.pt")
        self.streamName = streamName
        self.delay_thres = delay_thres
        self.alarm_thres = alarm_thres
        self.rtsp = rtsp
        
        self.is_live=False
    def warm_up(self, channel ,focus=None, image_size=None):
        self.focus = focus
        self.image_size = image_size

        source = self.rtsp + f'/cam/realmonitor?channel={channel}&subtype=0'
        print(source)
        self.vid = cv2.VideoCapture(source)
        self.stride, self.names, self.pt = self.stride, self.names, self.pt
        self.coords = json.load(open(f"./config/{self.streamName}_polygon.json", 'r'))[
            'coords']
        self.poly = Polygon(self.coords)
        
    def stop(self):
        self.sleep_time = 0
        self.is_live = False
    def performance(self):
        self.sleep_time = 0.0
    def balanced(self,sleep=0.1):
        self.sleep_time = sleep
    
    def start(self,conf_thres,iou_thres,max_det):
        self.is_live = True
        first = False
        last = True
        delay = 0
        alarm = 0
        self.balanced()
        
        while (True):
            start_time= time.time()
            for _ in range(5):
                ret, frame_org = self.vid.read()
            if not ret:
                continue
            
            frame = check_image_focus(
                frame_org, focus=self.focus, image_size=self.image_size)
            im = frame.transpose((2, 0, 1))[::-1]
            im = np.ascontiguousarray(im)
            im = torch.from_numpy(im)
            im = im.half() if self.fp16 else im.float()
            im /= 255.0
            im = im[None]

            pred = self(im)
            pred = non_max_suppression(pred, conf_thres=conf_thres, classes=[
                0], iou_thres=iou_thres, max_det=max_det)[0]

            center_points = find_center_points(np.asarray(pred))
            is_alarm = check_alarm(center_points, self.poly)
            if is_alarm > 0 or not last:
                if last and not first:
                    first = True
                    last = False
                    send_telegram(f"Có {is_alarm} người")
                else:
                    first = False
                if not is_alarm:
                    delay += 1
                    if delay > self.delay_thres:
                        last = True

                else:
                    delay = 0
                alarm += 1
                if alarm % self.alarm_thres == 0:
                    send_telegram(f"Có {is_alarm} người")

            else:
                first = False
                last = True
            # frame = draw_predict(frame, np.asarray(pred), center_points)
            # frame = draw_boudary(frame, np.asarray(self.coords))
            # cv2.imshow("frame", frame)
            # cv2.waitKey(1)
            
            if not self.is_live:
                # self.vid.release()
                # cv2.destroyAllWindows()
                break
            
            time.sleep(self.sleep_time)
            print("Time: ",time.time()-start_time, self.sleep_time)
            
            
config = {
    "streamName": "outHouse_Left",
    "rtsp": "rtsp://admin:Mot2345678@192.168.1.2:554",
    "channel":2,
    "focus":"left",
    "image_size": (512, 512),
    "model": {
        "conf_thres": 0.4,
        "iou_thres":0.3,
        "max_det":10,
        
    }
    
}
if __name__=='__main__':
    
    model = Model(streamName=config['streamName'],rtsp=config['rtsp'],delay_thres=5,alarm_thres=15)
    model.warm_up(channel=config['channel'],focus=config['focus'], image_size=config['image_size'])

    model.start(config['model']['conf_thres'],config['model']['iou_thres'],config['model']['max_det'])
    



