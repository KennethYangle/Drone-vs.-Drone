import multiprocessing
import ctypes
import time

def func(num):
    num.value = 0
    while 1:
        print(num.value)
        time.sleep(0.1)

if __name__ == "__main__":
    num = multiprocessing.Value('b', 1)
    print(num.value)

    p = multiprocessing.Process(target=func, args=(num,))
    p.start()
    # p.join()

    print(num.value)

    while 1:
        num.value += 1
        time.sleep(0.05)