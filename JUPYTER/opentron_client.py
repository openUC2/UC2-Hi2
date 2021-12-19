#!/usr/bin/env python
# coding: utf-8

"""
Simple client code for the Opentrons in Python - adapted from OFM Client 
Copyright 2020 Richard Bowman, released under LGPL 3.0 or later
Copyright 2021 Benedict Diederich, released under LGPL 3.0 or later
"""

import requests
import json
import time
import io
#import PIL.Image
import numpy as np
import logging
import zeroconf
import requests 
import json
#import matplotlib.pyplot as plt

ACTION_RUNNING_KEYWORDS = ["idle", "pending", "running"]
ACTION_OUTPUT_KEYS = ["output", "return"]

class OpentronsClient(object):
    headers = {'opentrons-version': '*'}

    def __init__(self, host, port=31950):
        if isinstance(host, zeroconf.ServiceInfo):
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
            #self.get_json(self.base_uri)
        logging.info(f"Connecting to microscope {self.host}:{self.port}")
        #self.populate_extensions()

    extensions = None
        
    @property
    def base_uri(self):
        return f"http://{self.host}:{self.port}"

    def get_json(self, path):
        """Perform an HTTP GET request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        r = requests.get(path)
        r.raise_for_status()
        return r.json()

    def post_json(self, path, payload={}):
        """Make an HTTP POST request and return the JSON response"""
        if not path.startswith("http"):
            path = self.base_uri + path
        r = requests.post(path, json=payload, headers=self.headers)
        r.raise_for_status()
        r = r.json()
        return r

    def toggle_light(self, state=True):
        """Turn on/off light of the robot"""
        payload = {
            "on":"true" if state else "false",
        }
        path = "/robot/lights"
        r = self.post_json(path, payload)
        return r
    

    def pipette_home(self, location="right"):
        #%% homing the robot
        payload = {
            "target": "robot",
            "mount": "right"
        }
        path = "/robot/home"
        r = self.post_json(path, payload)
        return r
    
    def positions(self):
        #%% get positions of robot
        path = "/robot/positions"
        r = self.get_json(path)
        return r
    
    #%% PIPETTE
    def add_pipette(self, name='p300_single', position='right'):
        # assign/add a pipette to the robot
        payload = {
            "name": name, 
            "position": position
        }
        path = '/hardware/pipette/add'
        r = self.post_json(path, payload)
        return r
    


    ''' 
    #
    First, start a “liveProtocol” session via HTTP:
    POST /sessions
    {
        "data": {
            "sessionType": "liveProtocol"
        }
    }

    This will return a `sessionId`. You can use this session ID to load a pipette and a labware:
    POST /sessions/:sessionId/commands/execute
    {
        "data": {
            "command": "equipment.loadPipette",
            "data": {
                "pipetteName": "p300_single",
                "mount": "right"
            }
        }
    }

    POST /sessions/:sessionId/commands/execute
    {
        "data": {
            "command": "equipment.loadLabware",
            "data": {
                "loadName": "opentrons_96_tiprack_300ul",
                "version": 1,
                "namespace": "opentrons",
                "location": { "slot": 5 }
            }
        }
    }

    Those responses will come back with a `result.pipetteId` and a `result.labwareId`, respectively, which you can use in future commands, like:
    POST /sessions/:sessionId/commands/execute
    {
        "data": {
            "command": "pipette.pickUpTip",
            "data": {
                "pipetteId": "b1c58fa0-7fea-43c7-b6da-f23525f8f66f",
                "labwareId": "a3d31c93-aeb5-45f5-8503-5a6993e925aa",
                "wellName": "A1"
            }
        }
    }
    ''' 



