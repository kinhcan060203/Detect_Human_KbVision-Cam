import cv2
from PIL import Image
import numpy as np
from shapely.geometry import Point, Polygon
import json
import requests


def send_telegram(message):
    TOKEN = "6862356964:AAFqV0hNBjMpdbkJ7Ai3Bcs-GoIql4CsCyA"
    chat_id = "-4021883249"
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    print(requests.get(url).json()['ok'])  # this sends the message


def check_image_focus(image, focus='full', image_size=None, auto=True):
    from yolov5.utils.augmentations import letterbox
    if focus == "left":
        image = image[:, :image.shape[0]]
    elif focus == "right":
        image = image[:, image.shape[1]-image.shape[0]:]
    if image_size:
        image = cv2.resize(image, image_size)
    else:
        image = letterbox(image, (512, 512), stride=1, auto=auto)[0]
    return image


def draw_predict(frame, xyxy_, center_points=[]):
    for i in range(len(xyxy_)):
        start_point = (int(xyxy_[i][0]), int(xyxy_[i][1]))

        end_point = (int(xyxy_[i][2]), int(xyxy_[i][3]))
        color = (255, 0, 0)
        thickness = 1

        frame = cv2.rectangle(frame, start_point,
                              end_point, color, thickness)
        if center_points:

            frame = cv2.circle(frame, (center_points[i][0], center_points[i][1]), radius=5, color=(
                0, 0, 255), thickness=-1)
    return frame


def draw_boudary(frame, xyxy_):
    for i in range(-1, len(xyxy_)-1):
        start_point = (int(xyxy_[i][0]), int(xyxy_[i][1]))
        end_point = (int(xyxy_[i+1][0]), int(xyxy_[i+1][1]))

        color = (255, 100, 0)
        thickness = 2

        frame = cv2.line(frame, start_point,
                         end_point, color, thickness)
    return frame


def find_center_points(points):
    end_points = []
    for point in points:
        x_c = int((point[0]+point[2])/2)
        y_c = int((point[1]+point[3])/2)
        end_points.append([x_c, y_c])
    return (end_points)


def check_alarm(center_points, poly):
    count_human = 0
    for point in center_points:
        point = Point(*point)
        if point.within(poly):
            count_human += 1
    return count_human
