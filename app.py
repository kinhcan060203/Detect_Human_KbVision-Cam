from flask import Flask,jsonify
from model import Model
import cv2
from flask_cors import CORS, cross_origin
import threading
app = Flask(__name__)
cors = CORS(app)


class App():
    def __init__(self,config,*args,**kwargs) -> None:
        
        self.config = config
        self.model = None
        self.model_threading = None
        self.var = {
            "status":"stop",
            "mode":"balanced"
        }
    def setup(self):
        streamName = self.config.get("streamName", "streamName")
        focus = self.config.get("focus","full")
        image_size = self.config.get("image_size",(512,512))
        rtsp = self.config.get("rtsp",'')
        channel = self.config.get("channel",1)

        try:
            stream = cv2.VideoCapture(rtsp)
            for _ in range(5):
                ret, image = stream.read()
                if not ret:
                    continue
                else:
                    break
                
            if not ret:
                raise("Could not read source image")
            self.model = self.__initiate(streamName=streamName,rtsp=rtsp,channel=channel,focus=focus,image_size=image_size)
            
        except Exception as e:
            print(e)
            raise(f"Could not connect source: {rtsp}")
        
        return self
    def __initiate(self,streamName,rtsp,channel,focus,image_size):
        model = Model(streamName=streamName,rtsp=rtsp,delay_thres=5,alarm_thres=15)
        model.warm_up(channel=channel,focus=focus, image_size=image_size)
        return model
 
    def __start(self):
        conf_thres = self.config['model'].get("conf_thres",0.4)
        iou_thres = self.config['model'].get("iou_thres",0.3)
        max_det = self.config['model'].get("max_det",10)
        
        if self.model_threading is None or not self.model_threading.is_alive():
            
            self.model_threading = threading.Thread(target=self.model.start, args=(conf_thres,iou_thres,max_det,))
            self.model_threading.daemon = True
            print("oke")
        self.model_threading.start()
        
        
    def __stop(self):
        self.model.stop()
        del self.model
        self.model = None
    
    def __performance(self):
        self.model.performance()
        
    def __balanced(self,sleep):
        self.model.balanced(sleep)
    def set_mode(self, mode: str,params: dict ={}):
        match mode:
            case "start":
                self.__start()
                self.var["status"] = "running"
            case "performance":
                self.__performance()
                self.var["mode"] = "performance"
            case "balanced":
                self.__balanced(params['sleep'])
                self.var["mode"] = "balanced"

            case "stop":
                self.__stop()
                self.var["status"] = "stop"
                
            case _:
                raise ValueError(f'Mode must in ["start", "performance", "balaced", and "stop"]')
            

#             response = {
    #     "status_code":200,
    #     "message":"OKe nha e iu init",
    #     "action":"ready",
    #     "detail":{
    #         "rtsp":f"rtsp://admin:Mot2345678@192.168.1.2:554/cam/realmonitor?channel={1}&subtype=0"
    #     }
    # }
def filter_response(status, status_code):
    response = {
        "status_code":status_code,
        "status":status,
        "detail":{}
    }
    if status_code==200:
        response["message"] = f"Camera {status} successfully !!!"
        response["detail"]["message"] = "Nothing"
    else:
        response["message"] = f"Camera {status} failed @@@"
        response["detail"]["message"] = f"Not allowed {status} Camera when is status {Camera.var['status']}"
    
    return jsonify(response)




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


allow_list_action = {
    "start":"ready",
    "initiate":"stop",
    "balanced":"running",
    "performance":"running",
    "stop":"running"
}
Camera = App(config)
model_threading = None
@app.route('/performance',methods=["POST"])
def performance():
    if Camera.var["status"] == allow_list_action["stop"]:
        Camera.set_mode("performance")

        return filter_response("performance",status_code=200)
    else:
        return filter_response("performance",status_code=404)
    
    
@app.route('/balanced/<sleep>',methods=["POST"])
def balanced(sleep):
    if Camera.var["status"] == allow_list_action["balanced"]:
        Camera.set_mode("balanced",{'sleep':float(sleep)})

        return filter_response("balanced",status_code=200)
    else:
        return filter_response("balanced",status_code=404)
    
    
    
@app.route('/stop',methods=["POST"])
def stop():
    if Camera.var["status"] == allow_list_action["stop"]:
        Camera.set_mode("stop")

        return filter_response("stop",status_code=200)
    else:
        return filter_response("stop",status_code=404)



@app.route('/start',methods=["POST"])
def start():
    
    if Camera.var["status"] == allow_list_action["start"]:
        print(Camera.var["status"])
        Camera.var["mode"] = "balanced"
        Camera.set_mode("start")
        import time
        while True:
            time.sleep(2)
            if Camera.var["status"] == "running":
                break
            print("as")
        return filter_response("running",status_code=200)
    else:
        return filter_response("start",status_code=404)





@app.route('/',methods=["GET", "POST"])

def hello():
    global Camera
    if Camera.var['status']=='stop':
        Camera.var['status']='pending'
        Camera.setup()
        Camera.var['status']='ready'
        
        return filter_response("ready",status_code=200)

    return filter_response("ready",status_code=404)




if __name__ == '__main__':
 
    app.run(port="5005")