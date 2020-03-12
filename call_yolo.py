import cv2
import os
def callYolo():
    """Return boundingbox\n
        drone_pose = [cx, cy, w, h]."""
    os.chdir('/home/zhenglong/github/darknet')
    # p = os.popen("./darknet detector test cfg/drone.data cfg/yolo-drone.cfg weights/yolo-drone.weights data/telloview.png")
    try:
        p = os.popen("./darknet detector test ./data/dropnet.data ./cfg/dropnet.cfg ./weights/dropnet_final.weights -thresh 0.1 -ext_output data/telloview.png")
        lines = p.readlines()
        nums = lines[-1].split(' ')
        drone_pose = []
        for num in nums:
            drone_pose.append(float(num))
        return drone_pose
    except Exception as ex:
        print(ex)
        print("Detection failed!\nPlease manually select the target")
        image = cv2.imread("data/telloview.png")
        r = cv2.selectROI(image, False, False)
        return [r[0]+r[2]/2, r[1]+r[3]/2, r[2], r[3]]

if __name__ == "__main__":
    callYolo()