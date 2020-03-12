import airsim
import numpy as np
import cv2
import rospy
from geometry_msgs.msg import Vector3

def objectDetect():
    tic = cv2.getTickCount()
    responses = client.simGetImages([
                airsim.ImageRequest("1", airsim.ImageType.Scene, False, False)])  #scene vision image in uncompressed RGBA array
    img1d = np.fromstring(responses[0].image_data_uint8, dtype=np.uint8) #get numpy array
    toc = cv2.getTickCount() - tic
    # print('Capture time: {:.1f}'.format(toc * 1000 / cv2.getTickFrequency())) # get and write total use 290ms

    img_rgba = img1d.reshape(responses[0].height, responses[0].width, 4) #reshape array to 4 channel image array H X W X 4
    img_bgr = cv2.cvtColor(img_rgba, cv2.COLOR_RGBA2BGR)
    hue_image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    low_range = np.array([0, 123, 100])
    high_range = np.array([5, 255, 255])
    th = cv2.inRange(hue_image, low_range, high_range)
    dilated = cv2.dilate(th, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=2)
    cv2.imshow("hsv", dilated)
    cv2.waitKey(1)
    M = cv2.moments(dilated)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    print(cX, cY)
    pub.publish(Vector3(responses[0].width/2-cX, responses[0].height/2-cY, 0))
    toc = cv2.getTickCount() - tic
    # print('Total time: {:.1f}'.format(toc * 1000 / cv2.getTickFrequency())) # get and write total use 290ms


client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
# client.armDisarm(True)

rospy.init_node('object_error')
pub = rospy.Publisher('error', Vector3, queue_size = 1)

airsim.wait_key('Press any key to detect')
while not rospy.is_shutdown():
    objectDetect()
