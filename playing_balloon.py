import sys
sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
import traceback
import tellopy
import av
import cv2
import time
import datetime
import numpy as np

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

def main():
    k_yaw = 0.003
    k_z = -0.005
    attack_pitch = 0.8
    # attack_pitch = 0
    min_prop = 0.00
    max_prop = 1
    servo_centre_x = 0.5
    servo_centre_y = 0.4

    # 0. get tello object, get video writer
    drone = tellopy.Tello()
    now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    path = './capture/' + now
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    cap_out = cv2.VideoWriter(path+'_balloon.avi', fourcc, 20.0, (960,720))

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
            sleep(5)
        except Exception as ex:
            print(ex)
        # skip first 300 frames
        frame_skip = 300
        while True:
            for frame in container.decode(video=0):
                # 3. get picture
                if 0 < frame_skip:
                    frame_skip = frame_skip - 1
                    continue
                start_time = time.time()
                image = cv2.cvtColor(np.array(frame.to_image()), cv2.COLOR_RGB2BGR)
                h,w,l = np.shape(image)
                cv2.imshow('Original', image)
                cap_out.write(image)
                cv2.waitKey(1)

                # 4. detection red
                hue_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
                low_range = np.array([170, 120, 120])
                high_range = np.array([180, 230, 225])
                th = cv2.inRange(hue_image, low_range, high_range)
                dilated = cv2.dilate(th, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), iterations=2)
                cv2.imshow("hsv", dilated)
                cv2.waitKey(1)
                M = cv2.moments(dilated, binaryImage = True)
                if M["m00"] != 0:
                    cX = int(M["m10"] / M["m00"])
                    cY = int(M["m01"] / M["m00"])
                    print(cX, cY)
                else:
                    print(-1, -1)

                if frame.time_base < 1.0/60:
                    time_base = 1.0/60
                else:
                    time_base = frame.time_base
                frame_skip = int((time.time() - start_time)/time_base)

                # 5. attack
                if M["m00"] > min_prop * w * h:
                    print(M["m00"], w*h)
                    drone.set_yaw(saturation(k_yaw * (cX - w * servo_centre_x)))
                    drone.set_throttle(saturation(k_z * (cY - h * servo_centre_y)))
                    if M["m00"] < max_prop * w * h:
                        drone.set_pitch(attack_pitch)
                    else:
                        drone.set_pitch(0)
                else:
                    drone.set_yaw(-0.5)
                    drone.set_throttle(0)
                    drone.set_pitch(0)

    except Exception as ex:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print(ex)
    finally:
        drone.land()
        drone.quit()
        cap_out.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
