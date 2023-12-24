from flask import Flask
from model import Model
import torch
import cv2
import numpy as np
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)



class App():
    def __init__(self,config,*args,**kwargs) -> None:
        
        self.config = self.__config(config)
        self.model = self.__initiate(streamName=self.streamName,rtsp=self.rtsp,channel=self.channel,focus=self.focus,image_size=self.image_size)
        
    def __config(self,config):
        self.streamName = config.get("streamName", "streamName")
        self.focus = config.get("focus","full")
        self.image_size = config.get("image_size",(512,512))
        self.rtsp = config.get("rtsp",'')
        self.channel = config.get("channel",1)
        
        self.conf_thres = config['model'].get("conf_thres",0.4)
        self.iou_thres = config['model'].get("iou_thres",0.3)
        self.max_det = config['model'].get("max_det",10)
        try:
            stream = cv2.VideoCapture(self.rtsp)
            for _ in range(5):
                ret, image = stream.read()
                if not ret:
                    continue
                else:
                    break
                
            if not ret:
                raise("Could not read source image")
        except Exception as e:
            raise(f"Could not connect source: {self.rtsp}")
    
    def __initiate(self,streamName,rtsp,channel,focus,image_size):
        model = Model(streamName=streamName,rtsp=rtsp,delay_thres=5,alarm_thres=15)
        model.warm_up(channel=channel,focus=focus, image_size=image_size)
        return model
 
    def __start(self):
        self.model.start(self.conf_thres,self.iou_thres,self.max_det)
    def __stop(self):
        self.model.stop()
    
    def __performence(self):
        self.model.performence()
        
    def __balanced(self,sleep):
        self.model.balanced(sleep)
    def set_mode(self, mode: str,params: dict ={}):
        """Set the mode of the application.

        Args:s
            mode (str): The mode to set the application to.
                methods are "start", "performence", "balaced", and "stop".

        Raises:
            ValueError: If an invalid mode is specified.
        """

        match mode:
            case "start":
                self.__start()
            case "performence":
                self.__performence()

            case "balanced":
                self.__balanced(params['sleep'])

            case "stop":
                self.__stop()
            case _:
                raise ValueError(f'Mode must in ["start", "performence", "balaced", and "stop"]')
cam_info = {
    "channels": {
        "inHouse": 1,
        "outHouse_Left": 2,
        "outHouse_Right": 4,
        "topHouse": 3
    }
}


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

var = {
    "status":"stop",
    "mode":"balanced"
}
allow_list_action = {
    "start":"ready",
    "initiate":"stop",
    "balanced":"running",
    "performence":"running",
    "stop":"running"
}
Camera=None

@app.route('/performence',methods=["POST"])
def performence():
    print("performence")
    if var["status"] == allow_list_action["stop"]:
        Camera.set_mode("performence")
        var["mode"] = "performence"
        return "Success!!"
    else:
        return f"Not allowed performence Camera when is status {var['status']}"
@app.route('/balanced/<sleep>',methods=["POST"])
def balanced(sleep):
    if var["status"] == allow_list_action["balanced"]:
        Camera.set_mode("balanced",{'sleep':float(sleep)})
        var["mode"] = "balanced"
        return "Success!!"
        
    else:
        return f"Not allowed balanced Camera when is status {var['status']}"
@app.route('/stop',methods=["POST"])
def stop():
    if var["status"] == allow_list_action["stop"]:
        Camera.set_mode("stop")
        var["status"] = "stop"
        
        return "Success!"

    else:
        return f"Not allowed stop Camera when is status {var['status']}"

@app.route('/start',methods=["POST"])
def start():
    if var["status"] == allow_list_action["start"]:
        var["mode"] = "balanced"
        var["status"] = "running"
        
        Camera.set_mode("start")
        
        return "Finished!"
    else:
        return f"Not allowed start Camera when is status {var['status']}"




@app.route('/',methods=["GET", "POST"])

def hello():
    global Camera
    global var
    
    if not Camera and var['status']=='stop':
        var['status']='pending'
        Camera = App(config)
        var['status']='ready'
    return 'Hello, Camera!!!'
if __name__ == '__main__':
 
    app.run()