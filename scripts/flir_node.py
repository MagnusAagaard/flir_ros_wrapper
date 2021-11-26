#!/usr/bin/env python3
import PySpin
import sys
import rospy
import numpy as np
from flir_backend import FlirCamera

from std_msgs.msg import Header, Bool
from sensor_msgs.msg import Image
from flir_ros_wrapper.msg import ThermalImage
import matplotlib.pyplot as plt

class FlirCameraNode:
    def __init__(self):
        self.__get_params()
        self.__init_subscribers()
        self.__init_publishers()
        self.cam = FlirCamera(cam_idx = self.cam_idx, img_format=self.img_format)

    def __get_params(self):
        # Default cam_idx = 0
        self.cam_idx = rospy.get_param('~cam_idx', 0)
        # Get rate
        rate = rospy.get_param('~frame_rate', 30)
        self.rate = rospy.Rate(rate)
        self.debug = rospy.get_param('~debug', False)
        # Default acquisition_mode is continous
        self.acquisition_mode = rospy.get_param('~acquisition_mode', 'cont')
        # Topic to publish data
        self.publish_topic = rospy.get_param('~publish_topic', '~image_raw')
        # Topic to trigger acquisition
        self.trigger_topic = rospy.get_param('~trigger_topic','')
        if not self.trigger_topic and self.acquisition_mode == 'trigger':
            rospy.logerr('Parameter \'trigger_topic\' is not provided and acquisition mode is set to trigger..')
            sys.exit(-1)
        # Wether to convert data to celcius or not
        self.convert_to_celcius = rospy.get_param('~to_celcius', True)
        # Image format either mono8 for visualization in Rviz or mono14 for reliable thermal data
        self.img_format = rospy.get_param('~img_format', 'mono14')
        if self.convert_to_celcius and not self.img_format == 'mono14':
            rospy.logwarn('Parameter \'to_celcius\' is set to true, but \'img_format\' is not set to \'mono14\'.. Changing \'img_format\' to \'mono14\'...')
            self.img_format = 'mono14'
        

    def __init_publishers(self):
        # Setup publisher
        if self.img_format == 'mono14':
            self.img_pub = rospy.Publisher(self.publish_topic, ThermalImage, queue_size=1)
        elif self.img_format == 'mono8':
            self.img_pub = rospy.Publisher(self.publish_topic, Image, queue_size=1)
        else:
            raise AttributeError('Not a valid img_format (\'mono8\' or \'mono14\').')
            sys.exit(-1)

    def __init_subscribers(self):
        # Setup subscribers
        rospy.Subscriber(self.trigger_topic, Bool, self.__trigger_cb, queue_size=1)

    def __trigger_cb(self, msg):
        # Trigger initiated, acquire and publish image
        if msg.data == True:
            self.acquire_and_publish()

    def run(self):
        if self.acquisition_mode == 'continous':
            while not rospy.is_shutdown():
                self.acquire_and_publish()
                self.rate.sleep()
        elif self.acquisition_mode == 'trigger':
            rospy.spin()
        else:
            rospy.logerr('Acquisition mode was not set to either continous or trigger.. Exiting..')
        self.cam.shutdown()

    def acquire_and_publish(self):
        # Acquire image and publish
        result, image_data = self.cam.acquire_image()
        if result:
            # Image acquired correctly
            if self.img_format == 'mono14':
                img = ThermalImage(header=Header(stamp=rospy.Time.now()))
                img.height, img.width = image_data.shape
                img.encoding = 'mono14'
                img.is_celcius = self.convert_to_celcius
                if self.convert_to_celcius:
                    image_data = self.cam.convert_raw_data_to_celcius(image_data)
                    img.data = image_data.flatten()
                else:
                    img.data = image_data.flatten()
                self.img_pub.publish(img)
            elif self.img_format == 'mono8':
                img_ori = Image(header=Header(stamp=rospy.Time.now()))
                img_ori.height, img_ori.width = image_data.shape
                img_ori.encoding = 'mono8'
                img_ori.step = img_ori.width
                img_ori.data = image_data.flatten().tolist()
                self.img_pub.publish(img_ori)
            
            if self.debug:
                rospy.loginfo('Maximum temperature in frame: {}'.format(np.max(image_data)))
                # Draws an image on the current figure
                plt.imshow(image_data, cmap='inferno')
                plt.colorbar(format='%.2f')
                # Interval in plt.pause(interval) determines how fast the images are displayed in a GUI
                # Interval is in seconds.
                plt.pause(0.001)
                # Clear current reference of a figure. This will improve display speed significantly
                plt.clf()
        else:
            if self.debug:
                rospy.loginfo('Unable to acquire image..')

def main():
    rospy.init_node('flir_cam_node', log_level=rospy.INFO)
    # Instantiate class
    flir_cam_node = FlirCameraNode()
    if flir_cam_node.cam.init_success:
        rospy.loginfo('Camera initialized, running..')
        flir_cam_node.run()
    else:
        rospy.loginfo('Unable to initialize camera. Exiting.')
        

if __name__ == "__main__":
    main()