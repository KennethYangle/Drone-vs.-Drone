import sys
sys.path.append("/home/zhenglong/DaSiamRPN/code")

import glob, cv2, torch
import numpy as np
from os.path import realpath, dirname, join

from net import SiamRPNBIG
from run_SiamRPN import SiamRPN_init, SiamRPN_track
from utils import get_axis_aligned_bbox, cxy_wh_2_rect

def loadNet():
    net = SiamRPNBIG()
    net.load_state_dict(torch.load('/home/zhenglong/DaSiamRPN/code/SiamRPNBIG.model'))
    net.eval().cuda()
    return net

def trackerInit(im, p, net):
    target_pos, target_sz = np.array([p[0], p[1]]), np.array([p[2], p[3]])
    state = SiamRPN_init(im, target_pos, target_sz, net)
    return state

def tracking(im, state, cap):
    """Return cx, cy"""
    state = SiamRPN_track(state, im)  # track
    res = cxy_wh_2_rect(state['target_pos'], state['target_sz'])
    cx, cy = res[0]+res[2]/2, res[1]+res[3]/2
    res = [int(l) for l in res]
    cv2.rectangle(im, (res[0], res[1]), (res[0] + res[2], res[1] + res[3]), (0, 255, 255), 3)
    cv2.imshow('SiamRPN', im)
    cap.write(im)
    cv2.waitKey(1)
    return cx, cy