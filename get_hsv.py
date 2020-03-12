import cv2
import numpy as np

def print_hsv(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(hue_image[y,x])

cv2.namedWindow('image')
cv2.setMouseCallback('image', print_hsv)
im = cv2.imread("/home/zhenglong/Desktop/Original_screenshot.png")
hue_image = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
cv2.imshow("image", im)
cv2.waitKey()