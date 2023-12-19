import numpy as np
import cv2
import json
from my_utils import check_image_focus
from var_env import rtsp
FINAL_LINE_COLOR = (0, 200, 200)
WORKING_LINE_COLOR = (127, 127, 127)


class PolygonDrawer(object):
    def __init__(self, rtsp, channel, focus='full', image_size=(512, 512)):
        self.window_name = "PolygonDrawer"
        self.source = f"{rtsp}/cam/realmonitor?channel={channel}&subtype=0"
        self.done = False
        self.focus = focus
        self.image_size = image_size
        self.current = (0, 0)
        self.points = []

    def on_mouse(self, event, x, y, buttons, user_param):

        if self.done:
            return

        if event == cv2.EVENT_MOUSEMOVE:
            self.current = (x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.done = True

    def run(self):
        stream = cv2.VideoCapture(self.source)
        for _ in range(10):
            ret, image = stream.read()
            if not ret:
                continue
        if not ret:
            exit(print("Not found video!!!"))
        image = check_image_focus(image, self.focus, self.image_size)
        cv2.imshow(self.window_name, image)
        cv2.waitKey(1)
        cv2.setMouseCallback(self.window_name, self.on_mouse)

        while (not self.done):

            if (len(self.points) > 0):
                cv2.polylines(image, np.array(
                    [self.points]), False, FINAL_LINE_COLOR, 2)
                cv2.line(image, self.points[-1],
                         self.current, WORKING_LINE_COLOR)
            cv2.imshow(self.window_name, image)
            if cv2.waitKey(50) == 27:  # ESC hit
                self.done = True

        if (len(self.points) > 0):
            cv2.fillPoly(image, np.array([self.points]), FINAL_LINE_COLOR)
        cv2.imshow(self.window_name, image)
        cv2.waitKey()

        cv2.destroyWindow(self.window_name)
        return image


cam_info = {
    "channels": {
        "inHouse": 1,
        "outHouse_Left": 2,
        "outHouse_Right": 4,
        "topHouse": 3
    }
}

if __name__ == "__main__":

    boundName = "topHouse"
    focus = None
    image_size = None
    channel = cam_info["channels"][boundName]
    pd = PolygonDrawer(rtsp=rtsp, channel=channel,
                       focus=focus, image_size=image_size)
    image = pd.run()
    if len(pd.points) >= 3:
        cv2.imwrite(f"config/{boundName}_polygon.png", image)
        print("Polygon = %s" % pd.points)
        with open(f"config/{boundName}_polygon.json", 'w', encoding="UTF-8") as f:
            json.dump({
                "coords": pd.points
            }, f, indent=4)
