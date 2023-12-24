import numpy as np
import cv2
import json
from my_utils import PolygonDrawer




cam_info = {
    "channels": {
        "inHouse": 1,
        "outHouse_Left": 2,
        "outHouse_Right": 4,
        "topHouse": 3
    }
}

if __name__ == "__main__":
    # rtsp://{user}:{password}@{kb-vision-id}:554
    rtsp = "rtsp://admin:Mot2345678@192.168.1.2:554"
    
    boundName = "outHouse_Left"
    focus = "left"
    image_size = (512,512)
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
