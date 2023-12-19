from my_utils import check_image_focus
from my_utils import draw_predict, draw_boudary, check_alarm, send_telegram, find_center_points
import json
from shapely.geometry import Point, Polygon
import torch
import cv2
import numpy as np

from yolov5.models.common import DetectMultiBackend
from yolov5.utils.general import non_max_suppression
from var_env import rtsp


class mainStream():

    def __init__(self, model, streamName, focus=None, image_size=None):
        self.model = model
        self.streamName = streamName
        self.focus = focus
        self.image_size = image_size

        self.delay_thres = 5
        self.alarm_thres = 15

    def initiate(self):
        channel = cam_info["channels"][self.streamName]
        source = rtsp + f'/cam/realmonitor?channel={channel}&subtype=0'
        print(source)
        self.vid = cv2.VideoCapture(source)
        self.stride, self.names, self.pt = model.stride, model.names, model.pt
        self.coords = json.load(open(f"config\{self.streamName}_polygon.json", 'r'))[
            'coords']
        self.poly = Polygon(self.coords)

    def run(self):

        first = False
        last = True
        delay = 0
        count = 0

        while (True):
            for _ in range(5):
                ret, frame_org = self.vid.read()
            if not ret:
                continue
            frame = check_image_focus(
                frame_org, focus=self.focus, image_size=self.image_size)
            im = frame.transpose((2, 0, 1))[::-1]
            im = np.ascontiguousarray(im)
            im = torch.from_numpy(im)
            im = im.half() if model.fp16 else im.float()
            im /= 255.0
            im = im[None]

            pred = model(im)
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
                count += 1
                if count % self.alarm_thres == 0:
                    send_telegram(f"Có {is_alarm} người")

            else:
                first = False
                last = True

            frame = draw_predict(frame, np.asarray(pred), center_points)
            frame = draw_boudary(frame, np.asarray(self.coords))

            cv2.imshow("frame", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.vid.release()
                cv2.destroyAllWindows()
                break


cam_info = {
    "channels": {
        "inHouse": 1,
        "outHouse_Left": 2,
        "outHouse_Right": 4,
        "topHouse": 3
    }
}

conf_thres = 0.4
iou_thres = 0.3
max_det = 10
img_size = (512, 512)


if __name__ == '__main__':

    model = DetectMultiBackend(weights="yolov5s.pt")
    stream = mainStream(model, streamName="outHouse_Left",
                        focus="left", image_size=img_size)
    stream.initiate()

    exit(stream.run())
