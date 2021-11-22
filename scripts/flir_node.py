#!/usr/bin/env python3
import PySpin
import rospy
import numpy as np
from flir_backend import FlirCamera

from std_msgs.msg import Header
from flir_ros_wrapper.msg import ThermalImage

class FlirCameraNode:
    def __init__(self):
        self.__get_params()
        #self.__init_subscribers()
        self.__init_publishers()
        self.cam = FlirCamera(cam_idx = self.cam_idx, convert_to_celcius=self.convert_to_celcius)

    def __get_params(self):
        # Default cam_idx = 0
        self.cam_idx = rospy.get_param('~cam_idx', 0)
        self.debug = rospy.get_param('~debug', False)
        # Default acquisition_mode is continous
        self.acquisition_mode = rospy.get_param('~acquisition_mode', 'cont')
        self.publish_topic = rospy.get_param('~publish_topic', '~image_raw')
        self.convert_to_celcius = rospy.get_param('~to_celcius', True)

    def __init_publishers(self):
        # Setup publisher
        self.img_pub = rospy.Publisher(self.publish_topic, ThermalImage, queue_size=1)

    def run_and_publish(self):
        # Acquire image and publish
        result, image_data = self.cam.acquire_image()
        if result:
            # Image acquired correctly
            img = ThermalImage(header=Header(stamp=rospy.Time.now()))
            img.height, img.width = image_data.shape
            img.encoding = '14bit'
            img.is_celcius = self.convert_to_celcius
            img.data = image_data.flatten()
            self.img_pub.publish(img)
            if self.debug:
                rospy.loginfo('Maximum temperature in frame: {}'.format(np.max(image_data)))
        else:
            if self.debug:
                rospy.loginfo('Unable to acquire image..')

def main():
    rospy.init_node('flir_cam_node', log_level=rospy.INFO)
    # Get rate
    rate = rospy.get_param('~frame_rate', 30)
    r = rospy.Rate(rate)
    # Instantiate class
    flir_cam_node = FlirCameraNode()
    if flir_cam_node.cam.init_success:
        rospy.loginfo('Camera initialized, running..')
        while not rospy.is_shutdown():
            flir_cam_node.run_and_publish()
            r.sleep()
        flir_cam_node.cam.shutdown()
    else:
        rospy.loginfo('Unable to initialize camera. Exiting.')
        

if __name__ == "__main__":
    main()