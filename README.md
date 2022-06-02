# flir_ros_wrapper
This package is a ROS wrapper for Flir Ax5 thermal cameras (e.g. A65). The package depends on Spinnaker SDK including the Python wrapper. This has been developed and tested under Ubuntu 18.04 with ROS Melodic and Python 3.6

## Package use
Note that Spinakker SDK should be setup correctly before using the package as described below under "Spinakker SDK setup".
To launch the camera connect it properly and run
```shell script
roslaunch flir_ros_wrapper flir_node.launch
```
This will launch the camera and publish image messages. Settings and parameters can be specified in the launch file.

## Spinakker SDK setup
Download Spinakker SDK from [https://www.flir.com/products/spinnaker-sdk/](https://www.flir.com/products/spinnaker-sdk/) for your corresponding architecture. Download both the standard SDK and the Python wrapper, e.g. 'spinnaker-2.5.0.80-Ubuntu18.04-amd64-pkg.tar.gz' and 'spinnaker_python-2.5.0.80-cp36-cp36m-linux_x86_64.tar.gz'. Note that 'cp36' means for Python 3.6 and the system architecture ('amd64/arm64') and e.g. x86_64 can be found by running
```shell script
dpkg --print-architecture
uname -i
```
When the corresponding installation files have been downloaded, extract the files
```shell script
tar -xf spinnaker-2.5.0.80-Ubuntu18.04-amd64-pkg.tar.gz
tar -xf spinnaker_python-2.5.0.80-cp36-cp36m-linux_x86_64.tar.gz
```
Before running the installation make sure that dependencies are met.
For __Ubuntu 18.04__:
```shell script
sudo apt-get install libavcodec57 libavformat57 libswscale4 libswresample2 libavutil55 libusb-1.0-0
```
and for __Ubuntu 20.04__:
```shell script
sudo apt-get install libavcodec58 libavformat58 libswscale5 libswresample3 libavutil56 libusb-1.0-0 libpcre2-16-0 libdouble-conversion3 libxcb-xinput0 libxcb-xinerama0
```
Navigate to the spinnaker-2.5... directory and run the installation
```shell script
sudo sh install_spinnaker.sh
```
Follow the installation procedure.\
Next install the Python wrapper by running the wheel
```shell script
python3 -m pip install spinnaker_python-2.5.0.80-cp36-cp36m-linux_x86_64.whl
```
Now the Spinakker SDK with Python wrapper should be correctly installed. This can be verified by importing the library in a Python shell 'import PySpin'.

### Disable Reverse Path Filtering (RPF)
In order for the camera to be detected properly, RPF must be disabled. This is a system security measure that helps avoid spoofing and DDOS attacks. It can either be disabled temporarily until system reboot or permanently.

To __TEMPORARILY__ disable reverse path filtering for a specific network adapter
until the next reboot, eg. eth1, run the following commands:
```shell script
sudo sysctl -w net.ipv4.conf.all.rp_filter=0
sudo sysctl -w net.ipv4.conf.default.rp_filter=0
```
If you don't want to disable RPF every time you have rebooted and need to use the camera, this can also be permanently disabled, but this also decrease security of your system, so be aware.

To __PERMANENTLY__ disable reverse path filtering:
sudo gedit /etc/sysctl.d/10-network-security.conf
```shell script
sudo gedit /etc/sysctl.d/10-network-security.conf
```
and then comment out the lines below:
>    \# Turn on Source Address Verification in all interfaces to\
>    \# in order to prevent some spoofing attacks.\
>    \#net.ipv4.conf.default.rp_filter=1\
>    \#net.ipv4.conf.all.rp_filter=1

and then reboot the computer (only for permanently disabling)

### Setup wired connection correctly
To connect to the Flir Ax5 camera through Ethernet cable the wired connection must be set up correctly. An easy way to do this is to open the Settings and go to Network and into Wired settings. Go to IPv4 tab and change the settings to "Link-Local Only". This will make sure the camera connects on the right subnet and so on.
![Link-Local Only settings](https://github.com/MagnusAagaard/flir_ros_wrapper/raw/main/images/linklocal.png "Link-Local Only settings")
To make sure the camera is connected properly (as the Flir Ax5 might be expecting a diffrent subnet and IP by default) open up SpinView
```shell script
spinview
```
Or run the binary at '/opt/spinnaker/bin/SpinView_QT' if the paths were not chosen to be set up in the installation process. If the device is on a wrong subnet, the device will show an error saying this. Simply right click the interface and click “Auto Force IP” which should change the default IP that the camera expects. It is now ready to use.
![Spinview wrong subnet error](https://github.com/MagnusAagaard/flir_ros_wrapper/raw/main/images/spinview.png "Spinview wrong subnet error")
