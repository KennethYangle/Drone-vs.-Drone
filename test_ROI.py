import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import cv2

path = "/home/zhenglong/ykyk/TelloPy/tellopy/dataCollection/img/20190903_173307/20190903_173307_111.jpg"
image = cv2.imread(path)
r = cv2.selectROI(image, False, False)
# r=[left_top_x, left_bottom_y, w, h]
print(r)