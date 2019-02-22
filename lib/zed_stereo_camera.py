#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Referenced to ZED SDK live_camera.py
'''
import cv2
import pyzed.camera as zcam
import pyzed.types as tp
import pyzed.core as core
import pyzed.defines as sl

import threading
import time
import os

class WebcamVideoStream:
    """
    Reference:
    https://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/
    """

    def __init__(self):
        self.vid = None
        self.out = None
        self.running = False
        self.detection_counter = {}
        self.CAMERA = 2
        self.FRAME = 1
        self.BGR = 0
        self.I420 = 1
        self.input_src = self.CAMERA
        self.input_format = self.BGR
        
        self.camera_settings = sl.PyCAMERA_SETTINGS.PyCAMERA_SETTINGS_BRIGHTNESS
        self.str_camera_settings = "BRIGHTNESS"
        self.step_camera_settings = 1
        return

    def __del__(self):
        if self.vid.is_opened():
            self.vid.release()
        if self.out is not None:
            self.out.release()
        return

    def mkdir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        return

    def get_fps_est(self):
        # Number of frames to capture
        num_frames = 120;

        # Start time
        start = time.time()
         
        # Grab x num_frames
        for i in range(0, num_frames) :
            ret, frame = self.vid.read()

        # End time
        end = time.time()

        # Time elapsed
        seconds = end - start

        # Calculate frames per second
        fps  = num_frames / seconds;

        return fps

    def start(self, src, width, height, output_image_dir='output_image', output_movie_dir='output_movie', output_prefix='output', save_to_file=False):
        """
        output_1532580366.27.avi
        output_file[:-4] # remove .avi from filename
        """
        output_file = output_movie_dir + '/' + output_prefix + '_' + str(time.time()) + '.avi'
        self.OUTPUT_MOVIE_DIR = output_movie_dir
        self.OUTPUT_IMAGE_DIR = output_image_dir

        # initialize the video camera stream and read the first frame
        init = zcam.PyInitParameters(camera_fps=60)
        #help(init)
        cam = zcam.PyZEDCamera()
        if not cam.is_opened():
            print("Opening ZED Camera...")
        self.vid = cam
        status = cam.open(init)
        if status != tp.PyERROR_CODE.PySUCCESS:
            
            # camera failed
            raise IOError(("Couldn't open zed stereo camera: %s."%repr(status)))
            exit()

        runtime = zcam.PyRuntimeParameters()
        self.mat = core.PyMat()
        self.runtime = zcam.PyRuntimeParameters()
        self.print_camera_information(cam)
        
        err = cam.grab(runtime)
        self.ret = (err == tp.PyERROR_CODE.PySUCCESS)
        if not self.ret:
            raise IOError(("Couldn't grab frame."))
            
        cam.retrieve_image(self.mat, sl.PyVIEW.PyVIEW_LEFT)
        self.frame = self.mat.get_data()
            
        #self.ret, self.frame = self.vid.read()
       
        # initialize the variable used to indicate if the thread should
        # check camera vid shape
        self.real_width = int(cam.get_resolution().width)
        self.real_height = int(cam.get_resolution().height)
        print("Start video stream with shape: {},{}".format(self.real_width, self.real_height))
        self.running = True

        """ save to file """
        if save_to_file:
            self.mkdir(output_movie_dir)
            fps = cam.get_camera_fps()

            # Estimate the fps if not set
            if(fps == 0):
                fps = self.get_fps_est()
                print("Estimated frames per second : {0}".format(fps))

            fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
            self.out = cv2.VideoWriter(output_file, int(fourcc), fps, (int(self.real_width), int(self.real_height)))
        
        self.vid = cam
        
        # start the thread to read frames from the video stream
        t = threading.Thread(target=self.update, args=())
        t.setDaemon(True)
        t.start()
        return self

    def getSize(self):
        return (self.real_width, self.real_height)

    def update(self):
        try:
            while self.running:
                err = self.vid.grab(self.runtime)
                self.ret = (err == tp.PyERROR_CODE.PySUCCESS)
                if self.ret:
                    self.vid.retrieve_image(self.mat, sl.PyVIEW.PyVIEW_LEFT)
                    self.frame = self.mat.get_data()

        except:
            import traceback
            traceback.print_exc()
            self.running = False
        finally:
            # if the thread indicator variable is set, stop the thread
            self.vid.close()
        return

    def read(self):
        # return the frame most recently read
        return self.frame

    def save(self, frame):
        # save to avi
        self.out.write(frame)
        return

    def stop(self):
        self.running = False
        if self.vid.is_opened():
            self.vid.release()
        if self.out is not None:
            self.out.release()

    def save_detection_image(self, int_label, cv_bgr, filepath):
        self.mkdir(self.OUTPUT_IMAGE_DIR+"/"+str(int_label))

        dir_path, filename = os.path.split(filepath)
        if not filename in self.detection_counter:
            self.detection_counter.update({filename: 0})
        self.detection_counter[filename] += 1
        # remove .jpg/.jpeg/.png and get filename
        if filename.endswith(".jpeg"):
            filehead = filename[:-5]
            filetype = ".jpeg"
        elif filename.endswith(".jpg"):
            filehead = filename[:-4]
            filetype = ".jpg"
        elif filename.endswith(".png"):
            filehead = filename[:-4]
            filetype = ".png"

        # save to file
        cv2.imwrite(self.OUTPUT_IMAGE_DIR+"/"+str(int_label)+"/"+filehead+"_"+str(self.detection_counter[filename])+filetype, cv_bgr)
        return
        
    def print_camera_information(self, cam):
        print("Resolution: {0}, {1}.".format(round(cam.get_resolution().width, 2), cam.get_resolution().height))
        print("Camera FPS: {0}.".format(cam.get_camera_fps()))
        print("Firmware: {0}.".format(cam.get_camera_information().firmware_version))
        print("Serial number: {0}.\n".format(cam.get_camera_information().serial_number))

