import PySpin
import matplotlib.pyplot as plt
import keyboard
import numpy

_continue_recording_backend_value = True

class FlirCamera:
    def __init__(self, cam_idx=0, img_format='mono14'):
        self.cam_idx = cam_idx
        self.img_format = img_format
        self.init_success = self.__init_cams()
        print("Init done with result {}".format(self.init_success))

    def __init_cams(self):
        # Retrieve singleton reference to system object
        self.system = PySpin.System.GetInstance()
        # Get current library version
        version = self.system.GetLibraryVersion()
        print('Library version: {}.{}.{}.{}'.format(version.major, version.minor, version.type, version.build))
        # Retrieve list of cameras from the system
        self.cam_list = self.system.GetCameras()
        self.num_cameras = self.cam_list.GetSize()
        print('Number of cameras detected: {}'.format(self.num_cameras))
        if self.num_cameras <= 0:
            print('Unable to detect any cameras..')
            return False
        elif self.cam_idx >= self.num_cameras:
            print('Cam index is larger than number of cameras detected.. Running camera 0 instead.')
            self.cam_idx = 0
        self.cam = self.cam_list[self.cam_idx]
        # Initialize camera
        self.cam.Init()
        # Retrieve GenICam nodemap
        self.nodemap = self.cam.GetNodeMap()
        # Setup parameters
        result = self.setup_parameters(self.cam, self.nodemap)
        if not result:
            self.shutdown()
        else:
            self.cam.BeginAcquisition()
        return result

    def shutdown(self):
        print('Shutting down..')
        #  Ending acquisition appropriately helps ensure that devices clean up
        #  properly and do not need to be power-cycled to maintain integrity.
        try:
            self.cam.EndAcquisition()
            # Deinitialize camera
            self.cam.DeInit()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
        # Delete instance
        del self.cam
        # Clear camera list before releasing system
        self.cam_list.Clear()
        # Release system instance
        self.system.ReleaseInstance()

    def acquire_image(self):
        """
        This function runs the camera after setup has been performed by constructing
        the base class FlirCamera and self.init_success = True.
        :return: result, Numpy array of acquired image
        rtype: bool, numpy array
        """
        result = True
        image = -1
        try:
            #self.cam.BeginAcquisition()
            image_result = self.cam.GetNextImage()
            #  Ensure image completion
            if image_result.IsIncomplete():
                print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                result = False
            else:
                # Getting the image data as a numpy array
                image = image_result.GetNDArray()
            #  Release image
            #
            #  *** NOTES ***
            #  Images retrieved directly from the camera (i.e. non-converted
            #  images) need to be released in order to keep from filling the
            #  buffer.
            image_result.Release()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            result = False

        return result, image

    def setup_parameters(self, cam, nodemap):
        # Set thermal properties of the Flir camera
        if not self.set_thermal_properties(nodemap):
            print("Unable to set thermal properties")
            return False
        # Set buffer handling of the Flir camera
        if not self.set_buffer_handling(cam.GetTLStreamNodeMap()):
            print("Unable to set buffer handling")
            return False
        # Set image acquisition mode
        if not self.set_image_acquisition_mode(nodemap):
            print("Unable to set image acquisition mode")
            return False
        return True

    def set_thermal_properties(self, nodemap):
        """
        This function sets the thermal properties of the AX5 to be able to get temperature readings.

        :param nodemap: Device nodemap.
        :type nodemap: INodeMap
        :return: True if successful, False otherwise.
        :rtype: bool
        """
        # Set the pixel format to 14 bit
        node_pixel_format = PySpin.CEnumerationPtr(nodemap.GetNode('PixelFormat'))
        if not PySpin.IsAvailable(node_pixel_format) or not PySpin.IsWritable(node_pixel_format):
            print('Unable to set pixel format.. Aborting...')
            return False
        node_pixel_format_mono14 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono14'))
        node_pixel_format_mono8 = PySpin.CEnumEntryPtr(node_pixel_format.GetEntryByName('Mono8'))
        if self.img_format == 'mono8':
            if not PySpin.IsAvailable(node_pixel_format_mono8) or not PySpin.IsReadable(node_pixel_format_mono8):
                print('Unable to set pixel format to mono8.. Trying mono14...')
                if not PySpin.IsAvailable(node_pixel_format_mono14) or not PySpin.IsReadable(node_pixel_format_mono14):
                    print('Unable to set pixel format to mono14.. Aborting...')
                    return False
        else:
            # Default mono14
            if not PySpin.IsAvailable(node_pixel_format_mono14) or not PySpin.IsReadable(node_pixel_format_mono14):
                print('Unable to set pixel format to mono14.. Aborting...')
                return False
        
        pixel_format_mono14 = node_pixel_format_mono14.GetValue()
        pixel_format_mono8 = node_pixel_format_mono8.GetValue()
        node_pixel_format.SetIntValue(pixel_format_mono8 if self.img_format == 'mono8' else pixel_format_mono14)

        # Set the temperature resolution to high
        node_temp_linear = PySpin.CEnumerationPtr(nodemap.GetNode('TemperatureLinearResolution'))
        if not PySpin.IsAvailable(node_temp_linear) or not PySpin.IsWritable(node_temp_linear):
            print('Unable to set temperature resolution.. Aborting...')
            return False
        node_temp_linear_high = PySpin.CEnumEntryPtr(node_temp_linear.GetEntryByName('High'))
        if not PySpin.IsAvailable(node_temp_linear_high) or not PySpin.IsReadable(node_temp_linear_high):
            print('Unable to set temperature resolution.. Aborting...')
            return False
        linear_high = node_temp_linear_high.GetValue()
        node_temp_linear.SetIntValue(linear_high)

        # Set the CMOS bit depth to 14/8
        node_bit_depth = PySpin.CEnumerationPtr(nodemap.GetNode('CMOSBitDepth'))
        if not PySpin.IsAvailable(node_bit_depth) or not PySpin.IsWritable(node_bit_depth):
            print('Unable to set CMOS bit depth.. Aborting...')
            return False
        node_bit_depth_14bit = PySpin.CEnumEntryPtr(node_bit_depth.GetEntryByName('bit14bit'))
        node_bit_depth_8bit = PySpin.CEnumEntryPtr(node_bit_depth.GetEntryByName('bit8bit'))
        if self.img_format == 'mono8':
            if not PySpin.IsAvailable(node_bit_depth_8bit) or not PySpin.IsReadable(node_bit_depth_8bit):
                print('Unable to set CMOS bit depth to 8 bit.. Aborting...')
                return False
        else:
            if not PySpin.IsAvailable(node_bit_depth_14bit) or not PySpin.IsReadable(node_bit_depth_14bit):
                print('Unable to set CMOS bit depth.. Aborting...')
                return False
        bit_depth14 = node_bit_depth_14bit.GetValue()
        bit_depth8 = node_bit_depth_8bit.GetValue()
        node_bit_depth.SetIntValue(bit_depth8 if self.img_format == 'mono8' else bit_depth14)

        # Turn on temperature linear mode
        node_temp_linear = PySpin.CEnumerationPtr(nodemap.GetNode('TemperatureLinearMode'))
        if not PySpin.IsAvailable(node_temp_linear) or not PySpin.IsWritable(node_temp_linear):
            print('Unable to set temperature linear mode.. Aborting...')
            return False
        node_temp_linear_on = PySpin.CEnumEntryPtr(node_temp_linear.GetEntryByName('On'))
        if not PySpin.IsAvailable(node_temp_linear_on) or not PySpin.IsReadable(node_temp_linear_on):
            print('Unable to set temperature linear mode.. Aborting...')
            return False
        node_on = node_temp_linear_on.GetValue()
        node_temp_linear.SetIntValue(node_on)

        return True

    def set_buffer_handling(self, sNodemap):
        # Change buffer handling mode to NewestOnly
        node_bufferhandling_mode = PySpin.CEnumerationPtr(sNodemap.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False
        # Retrieve entry node from enumeration node
        node_newestonly = node_bufferhandling_mode.GetEntryByName('NewestOnly')
        if not PySpin.IsAvailable(node_newestonly) or not PySpin.IsReadable(node_newestonly):
            print('Unable to set stream buffer handling mode.. Aborting...')
            return False
        # Retrieve integer value from entry node
        node_newestonly_mode = node_newestonly.GetValue()
        # Set integer value from entry node as new value of enumeration node
        node_bufferhandling_mode.SetIntValue(node_newestonly_mode)

        return True

    def set_image_acquisition_mode(self, nodemap):
        node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))
        if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
            print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
            return False

        # Retrieve entry node from enumeration node
        node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
        if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                node_acquisition_mode_continuous):
            print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
            return False
        # Retrieve integer value from entry node
        acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
        # Set integer value from entry node as new value of enumeration node
        node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

        print('Acquisition mode set to continuous...')

        return True

    def convert_raw_data_to_celcius(self, arr):
        '''
        Returns numpy array with data converted from mono14 to celcius.
        '''
        return arr * 0.04 - 273.15


def handle_close(evt):
    """
    This function will close the GUI when close event happens.

    :param evt: Event that occurs when the figure closes.
    :type evt: Event
    """

    global _continue_recording_backend_value
    _continue_recording_backend_value = False

def main():
    flir_cam = FlirCamera(cam_idx=0)
    if flir_cam.init_success:
        global _continue_recording_backend_value
        while _continue_recording_backend_value:
            result, image_data_celsius = flir_cam.acquire_image()
            if result:
                # Draws an image on the current figure
                plt.imshow(image_data_celsius, cmap='inferno')
                plt.colorbar(format='%.2f')
                # Interval in plt.pause(interval) determines how fast the images are displayed in a GUI
                # Interval is in seconds.
                plt.pause(0.001)
                # Clear current reference of a figure. This will improve display speed significantly
                plt.clf()
            # If user presses enter, close the program
            if keyboard.is_pressed('ENTER'):
                print('Program is closing...')
                input('Done! Press Enter to exit...')
                _continue_recording_backend_value = False
        flir_cam.shutdown()
    else:
        print('Unable to initialize camera.')
    

if __name__ == "__main__":
    main()