
# Software Guide

This guide assumes, you have assembled the microscope already.

### Preparing the microscope

- Plugin the powersupply in the Raspberry Pi (USB) and CNC Shield (12V)
- Connect the USB cable with the CNC Shield and Raspberry Pi
- Check all wires if there is a non-connected wire somewhere
- Place the microscope objective lens inside the objective slot
- Connect the raspberry Pi ribbon cable with the Raspberry Pi according to [this explanation](https://projects.raspberrypi.org/en/projects/getting-started-with-picamera)
- Get the tools you need to level the bed (Hex keys for M5 and M3)
- Place a multwell plate in the try and add some "gum" to avoid slipping of the well-plate

### Starting the openflexure microscope server

- connect the microscope to your computer using a LAN cable (or to your home network router)
- Open up a terminal (MAC/Linux) or command line propmt (CMD, windows)
- enter `ssh UC2@UC2Pal015`, where `UC2` is the username and `UC2Pal015` is the hostname
- if everything works correctly, the commandline asks you for the password which is: `youseetoo`
- after hitting enter, you are connected to the microscope using SSH
- go to the folder, where the microscope software sits and start the server:
	- `cd /home/UC2/OFM/openflexure-microscope-server/openflexure_microscope/api`
	- `python 3.7 app.py`
- If everything goes right, the server should start and outputs something like : `server started on http://localhost:5000`
- You can access this using your browser by typing:  `http://UC2Pal015:5000` the website for the microscope should appear



### Troubleshotting

**The camera does not work:**
Check all wired connections and their correct orientation and reboot.

**The Stage does not work:**
Check all connections (USB, 12V of CNC Shield) and the Settings which are accessible using:
`nano /home/UC2/OFM/openflexure-microscope-server/openflexure_microscope/openflexure/settings/microscope_configuration.json`

and have a look at the port and type of the stage:

```py
{
  "camera": {
    "type": "PiCamera"
  },
  "stage": {
    "port": "/dev/ttyACM0",
    "type": "grbl"
  }
}
```

If you have connected the stage properly and type `dmesg | tail` in the SSH terminal, you will receive something like:
```
UC2@UC2Pal015:~/OFM/openflexure-microscope-server/openflexure_microscope/openflexure/settings $ dmesg | tail
[87673.997032]  r5:60000013 r4:80109b18
[87673.997048] [<80109ae4>] (arch_cpu_idle) from [<80920660>] (default_idle_call+0x40/0x48)
[87673.997062] [<80920620>] (default_idle_call) from [<8015504c>] (do_idle+0x124/0x168)
[87673.997073] [<80154f28>] (do_idle) from [<80155368>] (cpu_startup_entry+0x28/0x30)
[87673.997084]  r10:00000000 r9:410fd034 r8:0000406a r7:80eaf350 r6:10c0387d r5:00000002
[87673.997090]  r4:0000008a r3:60000093
[87673.997102] [<80155340>] (cpu_startup_entry) from [<8010fd10>] (secondary_start_kernel+0x160/0x16c)
[87673.997116] [<8010fbb0>] (secondary_start_kernel) from [<001027cc>] (0x1027cc)
[87673.997124]  r5:00000055 r4:2f10806a
[87673.997136] ---[ end trace 715e6d19da8dbf53 ]---
```
where there will be something like `ttyACM0` or `ttyUSB1` representing the Arduino hosting the GRBL board. Use this for the settings above and add `/dev/` to it.

### First Use

1. Control
2. Page Up/down, scrol => Z stage
3. KEys x/y
4. homing



### Extensions



# Software

The software is based on already available open-source projects. We use `GRBL` for the hardware control using an Arduino and the `OpenFlexure Microscope Server` for the GUI and I/O control.

## Hardware control software for the motors/light sources


We use the GLBR code to control the microscope - so you can use it from any computer equipped with a serial (e.g. USB) connection. In order to make it work you "simply" need to flash the GBRL code which is also available on [Github](https://github.com/grbl/grbl/) on your Arduino Uno + CNC Shield V3. Therefore:
1. Connect it to the Computer using a USB cable
2. Open the arduino IDE
3. Copy the GRBL library in the Arduino Library folder
3. Open the `grblUpload.ino` Demo in the `EXAMPLES` folder and upload it

We slightly modified the standard GRBL firmware which to match the homing and PWM for laser/LEDs. You can find the [GRBL Library here](https://github.com/beniroquai/grbl/tree/master/grbl)

## GUI and general I/O using the Openflexure Microscope Server

The beautiful [openflexure microscope server](http://gitlab.com/openflexure/openflexure-microscope-server/-/tree/opentrons-grbl) developed by Bowman et al. hosts a number of very helpful features:

- Extending functionality using customized extensions
- Web browser-based control of the microscope (from any device)
- Native raspberry pi camera flatfielding
- Python/Javascript/VUE.js based
- User-friendly UI

### Setting up the Raspberry Pi

The people from OpenFlexure provide a ready-to-use SD-card which we are going to use here as a start. This makes it easier to start with all dependencies already installed. Therefore go ahead and perform the following steps:

1. Download the [OpenFlexure Lite image](https://build.openflexure.org/raspbian-openflexure/armhf/lite/latest)
2. Format a micro SD card (use rather large SD card, 64 GB) and "burn" the image on the SD card using e.g. Win32Disk on Windows or Etcher
3. Insert the SD card into the Raspberry PI  and let it boot
3.1 For further details please have a look [here](https://openflexure.org/projects/microscope/build#install-the-os)
4. If you are connected to the Pi using a LAN connection, you should be able to access it on `microscope.local` (e.g. SSH)
4.1 The credentials are:
- username: `pi`
- password: `openflexure`

### Connect Device to a WiFi Router

The easiest is to connect to a wifi hotspot created with your cellphone. Attention: It's not very fast for streaming.

```
sudo raspiconfig # -> setup wifi -> set country
# setup the SSID (e.g. Blynk)
# setup password e.g. 12345678)
```

Alternatively:
```
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
```
and add:
```
network={
	ssid="Blynk"
	psk="12345678"
	key_mgmt=WPA-PSK
}
```

Print the IP address:
```
ifconfig
```


### Replace the OFM Server version with our modified version

All the original OFM components are sitting in `/var/openflexure/`, where we don't have access to. We want to change that to have it modifiable. Therefore we need to unregister the OFM service and add our own git repository.

**Download and install the git:**

```
cd ~
git clone -b opentrons-grbl https://gitlab.com/beniroquai/openflexure-microscope-server
cd openflexure-microscope-server/openflexure_microscope/api
ATTENTION:
sudo rm -r static # we need to rebuild it this takes long, so we side-load it by building it on a computer or downloading it here:
wget static.zip # link will follow; gdrive: https://drive.google.com/file/d/1I15lDKNll91UxbFlYPiCGbfkYkHK_CM1/view?usp=sharing
unzip static.zip
```

**Stop the OFM Server which is still running**

```
ofm stop
```

**Setup the settings**

Make sure the stage is matching the GRBL one with the correct serial port by editing `nano ~/openflexure-microscope-server/openflexure_microscope/openflexure/settings

```py
{
  "camera": {
    "type": "PiCamera"
  },
  "stage": {
    "port": "/dev/ttyACM0",
    "type": "grbl"
  }
}
```

If you have connected the stage properly and type `dmesg | tail` in the SSH terminal, you will receive something like:
```
UC2@UC2Pal015:~/OFM/openflexure-microscope-server/openflexure_microscope/openflexure/settings $ dmesg | tail
[87673.997032]  r5:60000013 r4:80109b18
[87673.997048] [<80109ae4>] (arch_cpu_idle) from [<80920660>] (default_idle_call+0x40/0x48)
[87673.997062] [<80920620>] (default_idle_call) from [<8015504c>] (do_idle+0x124/0x168)
[87673.997073] [<80154f28>] (do_idle) from [<80155368>] (cpu_startup_entry+0x28/0x30)
[87673.997084]  r10:00000000 r9:410fd034 r8:0000406a r7:80eaf350 r6:10c0387d r5:00000002
[87673.997090]  r4:0000008a r3:60000093
[87673.997102] [<80155340>] (cpu_startup_entry) from [<8010fd10>] (secondary_start_kernel+0x160/0x16c)
[87673.997116] [<8010fbb0>] (secondary_start_kernel) from [<001027cc>] (0x1027cc)
[87673.997124]  r5:00000055 r4:2f10806a
[87673.997136] ---[ end trace 715e6d19da8dbf53 ]---
```
where there will be something like `ttyACM0` or `ttyUSB1` representing the Arduino hosting the GRBL board. Use this for the settings above and add `/dev/` to it.

### Start the Server

We will need to use the preinstalled python environment sitting here:
`/var/openflexure/application/openflexure-microscope-server/.venv/bin/python`, hence we spin up the server using this command:

```
cd ~/openflexure-microscope-server/openflexure_microscope/api/
/var/openflexure/application/openflexure-microscope-server/.venv/bin/python app.py
```

The server will output something like:
```
pi@microscope:~/openflexure-microscope-server/openflexure_microscope/api $ /var/openflexure/application/openflexure-microscope-server/.venv/bin/python app.py
WARNING:root:No config file found at /home/pi/openflexure/settings/microscope_settings.json. Creating...
INFO:root:Populating /home/pi/openflexure/settings/microscope_settings.json...
WARNING:root:No config file found at /home/pi/openflexure/settings/microscope_configuration.json. Creating...
INFO:root:Populating /home/pi/openflexure/settings/microscope_configuration.json...
INFO:root:Running with data path /home/pi/openflexure
INFO:root:Loading /home/pi/openflexure/settings/microscope_configuration.json...
INFO:root:Creating camera
INFO:root:setting zoom, centre [0.5 0.5], size 1.0
INFO:root:Setting stage
INFO:root:Trying SangaStage
INFO:root:Initialising ExtensibleSerialInstrument on port None
INFO:root:Updating ESI port settings
INFO:root:Opening ESI connection to port None
Auto-scanning ports
INFO:root:Trying port /dev/ttyAMA0
INFO:root:Creating serial.Serial instance...
INFO:root:Created Serial<id=0x73d7c330, open=True>(port='/dev/ttyAMA0', baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=False, rtscts=False, dsrdtr=False)
INFO:root:Testing communication to SangaBoard
INFO:root:Running firmware checks...
ERROR:root:We don't have a serial port to open, meaning you didn't specify a valid port.  Are you sure the instrument is connected?
WARNING:root:No compatible Sangaboard hardware found.
INFO:root:Handling fallbacks
INFO:root:Creating locks
INFO:root:Loading /home/pi/openflexure/settings/microscope_settings.json...
INFO:root:0 capture files found on disk
INFO:root:0 capture files successfully reloaded
INFO:root:Creating app
WARNING:root:No extension file found at /home/pi/openflexure/extensions/microscope_extensions. Creating...
INFO:root:Populating /home/pi/openflexure/extensions/microscope_extensions/defaults.py...
ERROR:root:Preferred capture path /home/pi/openflexure/data/micrographs is missing or cannot be written to. Restoring defaults.
INFO:root:0 capture files found on disk
INFO:root:0 capture files successfully reloaded
INFO:root:Starting OpenFlexure Microscope Server...
Registering zeroconf 4a2c735e300aa5cae894fc4625f157a7a9b34edc._labthing._tcp.local.
Starting LabThings WSGI Server
Debug mode: False
Running on http://localhost:5000 (Press CTRL+C to quit)
```



You will be able to see the server in the browser by navigating to `http://microscope:5000`

<p align="left">
<a href="#logo" name="logo"><img src="./IMAGES/ofm_imjoy.gif" width="600"></a>
</p>

### Closing the server

Hit `ctrl + c` and the shell will give you:

```
^CUnregistering zeroconf services...
Server stopped
INFO:root:Loading /home/pi/openflexure/settings/microscope_settings.json...
INFO:root:Saving /home/pi/openflexure/settings/microscope_settings.json...
INFO:root:Closing <openflexure_microscope.microscope.Microscope object at 0x73e1aa10>
INFO:root:Stopped MJPEG stream on port 1. Switching to (3280, 2464).
INFO:root:Closed <openflexure_microscope.camera.pi.PiCameraStreamer object at 0x73d6ad90>
INFO:root:Closing <openflexure_microscope.captures.capture_manager.CaptureManager object at 0x73f966f0>
INFO:root:Closed <openflexure_microscope.microscope.Microscope object at 0x73e1aa10>
```



## Building the server

If you want to change anything to the server, please have a look at the original descritpion for the OFM server [here](https://gitlab.com/openflexure/openflexure-microscope-server/-/blob/master/README.md)
