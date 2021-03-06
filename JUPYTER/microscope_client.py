"""
Simple client code for the OpenFlexure Microscope in Python

Copyright 2020 Richard Bowman, released under LGPL 3.0 or later
"""

import requests
import json
import time
import io
#import PIL.Image
import numpy as np
import logging
import zeroconf
import pickle

ACTION_RUNNING_KEYWORDS = ["idle", "pending", "running"]
ACTION_OUTPUT_KEYS = ["output", "return"]

class MicroscopeClient(object):
    def __init__(self, host, port=5000, is_simulate = False):
        self.is_simulate = is_simulate
        if not self.is_simulate:
            if False: # isinstance(host, zeroconf.ServifceInfo):
                # If we have an mDNS ServiceInfo object, try each address
                # in turn, to see if it works (sometimes you get addresses
                # that don't work, if your network config is odd).
                # TODO: figure out why we can get mDNS packets even when
                # the microscope is unreachable by that IP
                for addr in host.parsed_addresses():
                    if ":" in addr:
                        self.host = f"[{addr}]"
                    else:
                        self.host = addr
                    self.port = host.port
                    try:
                        self.get_json(self.base_uri)
                        break
                    except:
                        logging.info(f"Couldn't connect to {addr}, we'll try another address if possible.")
            else:
                self.host = host
                self.port = port
                self.get_json(self.base_uri)
            logging.info(f"Connecting to microscope {self.host}:{self.port}")
            self.populate_extensions()
        else:
            print("Microscope is in simulation mode")

            
    extensions = None
        
    @property
    def base_uri(self):
        return f"http://{self.host}:{self.port}/api/v2"

    def get_json(self, path):
        """Perform an HTTP GET request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        r = requests.get(path)
        r.raise_for_status()
        return r.json()

    def post_json(self, path, payload={}, wait_on_task="auto"):
        """Make an HTTP POST request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        r = requests.post(path, json=payload)
        r.raise_for_status()
        r = r.json()
        if wait_on_task == "auto":
            wait_on_task = is_a_task(r)
        if wait_on_task:
            return poll_task(r)
        else:
            return r

    def populate_extensions(self):
        """Get the list of extensions and store it in self.extensions"""
        extension_list = self.get_json("/extensions/")
        self.extensions = {v["title"]: MicroscopeExtension(v) for v in extension_list}

    @property
    def position(self):
        """Return the position of the stage as a dictionary"""
        if self.is_simulate:
            response = {
              "x": 0,
              "y": 0,
              "z": 0
            }
        else:
            response = self.get_json("/instrument/state/stage/position")
        return response
    
    def get_position_array(self):
        """Return the position of the stage, as an array"""
        pos = self.position
        return np.array([pos[k] for k in "xyz"])
    
    def move(self, position, absolute=True, blocking=True):
        """Move the stage to a given position.

        WARNING! If you specify zeros, the stage might move a long way, as
        the default is absolute moves.  Position should be a dictionary
        with keys called "x", "y", and "z", although we will (for now) also
        accept an iterable of three numbers.
        """
        try:
            pos = {k: int(position[k]) for k in ["x", "y", "z"]}
        except:
            pos = {k: int(position[i]) for i, k in enumerate(["x", "y", "z"][:len(position)])}
        pos['absolute'] = absolute
        pos['blocking'] = blocking
        if not self.is_simulate:
            return self.post_json("/actions/stage/move", pos)
        
    def move_rel(self, position):
        """Move the stage by a given amount.  Zero should not move.
        
        This function calls ``move`` with ``absolute=False``
        """
        self.move(position, absolute=False)
        
    def query_background_task(self, task):
        """Request the status of a background task"""
        r = requests.get(task['links']['self']['href'])
        r.raise_for_status()
        return r.json()

    def capture_image_to_disk(self, params: dict = None):
        """Capture an image and save it to disk"""
        payload = {
            "use_video_port": True,
            "bayer": False,
            "temporary" :False
        }
        if params:
            payload.update(params)
        
        if not self.is_simulate:
            return requests.post(self.base_uri + "/actions/camera/capture", json=payload)
        
    def grab_image_np(self):
        """Capture a raw image and return it as a numpy array""" 
        if not self.is_simulate:
            r = requests.get(self.base_uri + "/streams/snapshot_raw")
            r.raise_for_status()
            serialized =  r.content
            return pickle.loads(serialized)
        else:
            return np.random.randi(100,100)

    def grab_image_raw(self):
        if not self.is_simulate:
            r = requests.get(self.base_uri + "/streams/snapshot")
            r.raise_for_status()
            return r.content
        else:
            return np.random.randi(100,100)
    
    def capture_image(self, params: dict = None):
        """Capture an image and return it as a PIL image object"""
        payload = {
            "use_video_port": True,
            "bayer": False,
        }
        if params:
            payload.update(params)
        r = requests.post(self.base_uri + "/actions/camera/ram-capture", json=payload, headers={'Accept': 'image/jpeg'})
        r.raise_for_status()
        image = PIL.Image.open(io.BytesIO(r.content))
        return image
    
    def grab_mjpeg(self, timeout, output=None, stop_event=None, max_size=None):
        """Capture the mjpeg stream from the camera"""
        if output is None:
            output = io.BytesIO()
        logging.debug("connecting to MJPEG stream")
        r = requests.get(self.base_uri + "/streams/mjpeg", stream=True)
        logging.debug("MJPEG request made")
        r.raise_for_status()
        logging.debug("Stream opened OK")

        start_time = time.time()
        received_bytes = 0
        for chunk in r.iter_content(chunk_size=1024):
            output.write(chunk)
            received_bytes += len(chunk)
            if timeout is not None and time.time() - start_time > timeout:
                break
            if stop_event is not None and stop_event.is_set():
                break
            if max_size is not None and received_bytes > max_size:
                break
        return output.getvalue()
    
    def record_video(self, video_format= "h264", video_framerate=30,video_length=100):
        payload = {
          "move_x": 0,
          "video_format": video_format,
          "video_framerate": video_framerate,
          "video_length": video_length
        }
        self.extensions['org.openflexure.video_extension']['video_api'].post_json(payload)


    def capture_image_to_disk(self, params: dict = None):
        """Capture an image and save it to disk"""
        payload = {
            "use_video_port": True,
            "bayer": False,
            "temporary" :False
        }
        if params:
            payload.update(params)
        r = requests.post(self.base_uri + "/actions/camera/capture", json=payload)
        return r

    def grab_image(self):
        """Grab an image from the stream and return as a PIL image object"""
        image = PIL.Image.open(io.BytesIO(self.grab_image_raw()))
        return image

    def grab_image_array(self, ):
        """Grab an image and return it as a numpy ndarray"""
        return np.array(self.grab_image())

    def move_and_measure(self, params: dict):
        """Move in z and track the JPEG size against time"""
        return self.extensions["org.openflexure.autofocus"]["move_and_measure"].post_json(params)

    def calibrate_xy(self):
        """Move the stage in X and Y to calibrate stage movements vs camera coordinates
        
        NB this takes around 2 minutes to complete with a 40x objective.  Lower magnification
        may work less well.
        """
        return self.extensions["org.openflexure.camera_stage_mapping"]["calibrate_xy"].post_json()

    def home(self):
        print("Microscope is homing...")
        if not self.is_simulate:
            payload = {
              "n_scans": 1,
              "task_name": "Homing"
            }
            self.extensions['org.openflexure.stagecalib_extension']['stage_calib_api'].post_json(payload)


    def plate_shaking(self, time_shaking):
        print("Microscope is shaking...")
        if not self.is_simulate:
            payload = {
              "n_scans": time_shaking,
              "task_name": "Plate-Shaking"
            }
            self.extensions['org.openflexure.stagecalib-extension']['stage_calib_api'].post_json(payload)
     
        
        
    def set_laser_led(self, i_laser=0, i_led=0):
        if not self.is_simulate:
            payload = {
              "i_laser": i_laser,
              "i_led": i_led
            }
            print("Setting Laser/LED to:", i_laser, i_led)
            self.extensions['org.openflexure.laser_extension']['laser_api'].post_json(payload)

    def autofocus_coarse(self, dz=1000, nz=11, is_uselight=False):
        '''
        dz is the distance +/- z the focus will search for highest contrast/sharpness
        nz is the number of stepp it will search for the focus 
        '''
        if not self.is_simulate:
            payload = {'dz': list(np.linspace(-dz,dz,nz))}
            #print("Focusing: "+str(payload))
            self.extensions["org.openflexure.autofocus"]["autofocus"].post_json(payload)
            return int(self.position['z'])
        else:
            return -1

    def autofocus(self, dz):
        """Move the stage up and down, and pick the sharpest position."""
        if not self.is_simulate:
            params={'dz': dz}
            return self.extensions["org.openflexure.autofocus"]["fast_autofocus"].post_json(params)
        else:
            return -1        

    def laplacian_autofocus(self, params: dict):
        """run a slower autofocus at heights dz respective to the starting point"""
        return self.extensions["org.openflexure.autofocus"]["autofocus"].post_json(params)

    def scan(self, params: dict, wait_on_task=True):
        """autofocus_dz: 20 is roughly fine, 30 is roughly medium"""
        return self.extensions["org.openflexure.scan"]["tile"].post_json(params, wait_on_task=wait_on_task)

    def grab_image_size(self):
        file_bytes = io.BytesIO(self.grab_image_raw())
        value = file_bytes.getvalue()
        length_size = len(value)
        return length_size

    @property
    def configuration(self):
        """Return the position of the stage as a dictionary"""
        return self.get_json("/instrument/configuration/")

class MicroscopeExtension():
    """A class that represents a microscope extension"""
    def __init__(self, extension_dict):
        self.extension_dict = extension_dict

    @property
    def links(self):
        return self.extension_dict["links"]
        
    def __getitem__(self, attr):
        """Dictionary-style syntax to get the links"""
        if attr not in self.links:
            raise KeyError(f"This extension does not have a link called {attr}.")
        link = self.links[attr]
        return RequestableURI(**link)

class RequestableURI():
    def __init__(self, href, description=None, methods=None):
        """A class representing an endpoint, making it easy to make requests to said endpoint."""
        self.href = href
        self.description = description or ""
        self.methods = methods or ['GET','POST',] #TODO: what's the sensible default?

    def get_json(self):
        """Perform an HTTP GET request and return the JSON response"""
        if "GET" not in self.methods:
            raise KeyError("This URI does not support GET requests")
        r = requests.get(self.href)
        r.raise_for_status()
        return r.json()

    def post_json(self, payload=None, wait_on_task="auto"):
        """Make an HTTP POST request and return the JSON response"""
        if "POST" not in self.methods:
            raise KeyError("This URI does not support POST requests")
        r = requests.post(self.href, json=payload or {})
        r.raise_for_status()
        r = r.json()
        if wait_on_task == "auto":
            wait_on_task = is_a_task(r)
        if wait_on_task:
            return poll_task(r)
        else:
            return r

def task_href(t):
    """Extract the endpoint address from a task dictionary"""
    return t["links"]["self"]["href"]

def is_a_task(t):
    """Return true if a parsed JSON return value represents a task"""
    self_href = task_href(t)
    try:
        return ("/api/v2/tasks/" in self_href or "/api/v2/actions/" in self_href)
    except:
        return False

def poll_task(task):
    """Poll a task until it finishes, and return the return value"""
    assert is_a_task(task), ("poll_task must be called with a "
                "parsed JSON representation of a task")
    log_n = 0
    while task["status"] in ACTION_RUNNING_KEYWORDS:
        r = requests.get(task_href(task))
        r.raise_for_status()
        task = r.json()
        while len(task["log"]) > log_n:
            d = task["log"][log_n]
            logging.log(d["levelno"], d["message"])
            log_n += 1
    for output_key in ACTION_OUTPUT_KEYS:
        if output_key in task:
            return task[output_key]
    return None

def find_mdns_services(type, timeout=10, n_services=9999):
    """Look for mdns services matching `type`.

    We will stop either after `timeout` seconds, or after
    `n_services` services have been found.
    """
    zc = zeroconf.Zeroconf()
    class Listener():
        def __init__(self):
            self.services_discovered = []

        def add_service(self, zeroconf, type, name):
            info = zeroconf.get_service_info(type, name)
            self.services_discovered.append(info)
    listener = Listener()
    browser = zeroconf.ServiceBrowser(zc, type, listener)
    stop_time = time.time() + timeout
    while len(listener.services_discovered) < n_services \
        and time.time() < stop_time:
        time.sleep(0.1)
    zc.close()
    return listener.services_discovered

def find_microscopes(timeout=10, n_microscopes=99999, microscope_hostname="_openflexure._tcp.local."):
    """Look for microscopes on the network.

    We will wait for responses, either for `timeout` seconds, or 
    until `n_microscopes` have been found.
    """
    return find_mdns_services(
        microscope_hostname, timeout, microscope_hostname="_openflexure._tcp.local.")

def find_first_microscope(timeout=10,microscope_hostname="_openflexure._tcp.local."):
    """Returnt the first microscope we can find on the network"""
    microscopes = find_microscopes(timeout, 1, microscope_hostname)
    if len(microscopes) == 0:
        raise Exception("There are no microscopes advertised on the local network")
    return MicroscopeClient(microscopes[0])

def iterate_mjpeg_frames_raw(buffer):
    """Given a captured MJPEG stream, iterate through the frames."""
    while True:
        start = buffer.find(b'\xff\xd8')
        if start > 0:
            logging.debug(f"Found {start} bytes of junk between JPEG frames")
        end = buffer.find(b'\xff\xd9')
        if start != -1 and end != -1:
            jpg = buffer[start:end+2]
            buffer = buffer[end+2:]
            logging.debug(f"Got a JPEG frame with {len(jpg)} bytes")
            yield jpg
        else:
            logging.debug(f"There were {len(buffer)} bytes left over from the MJPEG stream")
            return
'''
def iterate_mjpeg_images(buffer):
    for frame in iterate_mjpeg_frames_raw(buffer):
        yield PIL.Image.open(io.BytesIO(frame))
'''