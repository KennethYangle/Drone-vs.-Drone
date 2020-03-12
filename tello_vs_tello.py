import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import traceback
import tellopy
import av
import cv2
import time
import mmap
import multiprocessing
import datetime
import numpy as np
from collections import deque
from scipy import io

from call_yolo import callYolo
from call_siam import *

"""mission.value:\n
    0   idle
    1   wait
    2   attack
    """

# save ex, ey
target_vel = 0
mat_ex_0 = []
mat_ey_0 = []

def handler(event, sender, data, **args):
    drone = sender
    if event is drone.EVENT_FLIGHT_DATA:
        print(data)

def saturation(x):
    if x > 1.0:
        x = 1.0
    elif x < -1.0:
        x = -1.0
    return x

def droneSetup(mission, ex, ey):
    """Subprocess.\n
    Takeoff drone and write image to mmap."""
    # 0. get tello object
    drone = tellopy.Tello()
    # 0.1. parameters
    k_yaw = 0.002
    k_z = -0.005
    attack_pitch = 0.6
    min_prop = 0.00
    max_prop = 1

    # 1. connect
    try:
        drone.connect()
        drone.wait_for_connection(60.0)

        retry = 3
        container = None
        while container is None and 0 < retry:
            retry -= 1
            try:
                container = av.open(drone.get_video_stream())
            except av.AVError as ave:
                print(ave)
                print('retry...')

        # 2. takeoff
        try:
            drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
            drone.takeoff()
            drone.up(1)
            # time.sleep(5)
        except Exception as ex:
            print(ex)

        # 3. get image and write
        while True:
            for frame in container.decode(video=0):
                image = cv2.cvtColor(np.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                image_share = image.tostring()

                m.seek(0)
                m.write(image_share)
                m.flush()

                if mission.value == 0:
                    continue
                elif mission.value == 1:
                    continue
                elif mission.value == 2:
                    # 4. attack
                    drone.set_yaw(saturation(k_yaw * ex.value))
                    drone.set_throttle(saturation(k_z * ey.value))
                    drone.set_pitch(attack_pitch)
                    # drone.set_pitch(0)
                print(mission.value, ex.value, ey.value)

                # 5. esc
                key = cv2.waitKey(1)
                if key == 27:
                    drone.land()
                    drone.quit()
                    cv2.destroyAllWindows()

    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        io.savemat("./data/mat_ex_{0}_".format(target_vel)+now+".mat", {"matrix": mat_ex_0})
        io.savemat("./data/mat_ey_{0}_".format(target_vel)+now+".mat", {"matrix": mat_ey_0})
        drone.land()
        drone.quit()
        cv2.destroyAllWindows()
        # cap_out.release()


if __name__ == '__main__':
    # 0.0. shared memory and shared value
    image_length = 960*720*3
    m = mmap.mmap(-1, image_length)

    mission = multiprocessing.Value('b', 0)
    ex = multiprocessing.Value('d', 0.0)
    ey = multiprocessing.Value('d', 0.0)

    # 0.1. define the storage path and create VideoWriter object
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    path = './capture/' + now
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    cap_out = cv2.VideoWriter(path+'.avi', fourcc, 20.0, (960,720))

    # 0.2. parameters
    servo_centre_x = 0.5
    servo_centre_y = 0.4

    # 0.3. start drone process
    p = multiprocessing.Process(target=droneSetup, args=(mission,ex,ey))
    p.start()
    print("Sub-process start.")

    # 0.4. load SiamRPN
    net = loadNet()
    time.sleep(20)

    try:

        frame_cnt = 0
        while 1:
            # 1.0. get image from mmap
            m.seek(0)
            image_share = m.read(image_length)
            image = np.fromstring(image_share, dtype=np.uint8).reshape(720, 960, 3)
            frame_cnt = frame_cnt + 1

            # 1.1. skip first 300 frame
            if frame_cnt < 300:
                continue

            # 1.2. resize image to speed up
            # image = cv2.resize(image, (480,360))
            h,w,l = np.shape(image)

            # 2. use yolo to get object in first frame; tracker init
            if frame_cnt == 300:
                tic = cv2.getTickCount()
                cv2.imwrite("/home/zhenglong/github/darknet/data/telloview.png", image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                p = callYolo()
                print("initial potion: {0}".format(p))
                tracker_state = trackerInit(image, p, net)
                toc = cv2.getTickCount() - tic
                print("Initial time: {:.1f}".format(toc * 1000 / cv2.getTickFrequency()))   # 60ms when 960*720, 55ms when 480*360
                continue

            # 3. use Siam tracking
            tic = cv2.getTickCount()
            cx, cy = tracking(image, tracker_state, cap_out)
            toc = cv2.getTickCount() - tic
            print("Tracking time: {:.1f}".format(toc * 1000 / cv2.getTickFrequency()))

            # 4. change state
            mission.value = 2
            ex.value = cx - w * servo_centre_x
            ey.value = cy - h * servo_centre_y
            
            # 5. append
            mat_ex_0.append(ex.value)
            mat_ey_0.append(ey.value)

    except:
        io.savemat("./data/mat_ex_{0}_".format(target_vel)+now+".mat", {"matrix": mat_ex_0})
        io.savemat("./data/mat_ey_{0}_".format(target_vel)+now+".mat", {"matrix": mat_ey_0})