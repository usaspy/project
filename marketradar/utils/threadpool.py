import queue
import threading

class ThreadPool(object):
    def __init__(self,max_num=20):
        self.queue = queue.Queue(max_num)
        for i in range(max_num):
            self.queue.put(threading.Thread)

    def get_thread(self):
        return self.queue.get()

    def add_thread(self):
        self.queue.put(threading.Thread)

    def show_thread_nums(self):
        print(self.queue.maxsize)