import time
import serial
import numpy as np
import fnmatch
import re
import concurrent.futures
import concurrent


from openflexure_microscope.stage.stepper import StepMotor 



class nejeboard:
    is_homing = True                # do you want to do a homing on a restart?
    is_debug = True                # flag to switch on/off debugging messages
    is_homing_in_progress = False   # state if homing is in progress
    is_moving = False
    currentposition = (0,0,0) # XYZ
 
    steps_per_mm_x = 1 # how many revolution per fiven distnace => steps/mm
    steps_per_mm_y = 1 # Steps-per-Revolution*microsteps/mm per revolution
    steps_per_mm_z = 64 # 320 # in our case: 200*16*2mm= 6400

    speed = 1 # chosse between slow=1.. fast =4

    board = 'Neje'
    firmware = '3.2'
    position = [0,0,0] # xyz
    backlash = 0

    is_serial_open = False
	
    def __init__(self, serialport = "/dev/ttyUSB1",
                 currentposition=currentposition, backlash=backlash):
        self.port = "/dev/ttyUSB1" # serialport
        self.baudrate = 57600
        self.backlash = backlash

        # init z-motor connected to the GPIOs
        StepMotor.setmode()
        self.motor_z = StepMotor((12,16,20,21))
        
        
        self.initserial()

    def close(self):
        """ CLose Serial Connection"""
        self.serialport.flushInput()
        self.serialport.flushOutput()
        self.serialport.close()        

    def initserial(self):
        """ Initiliazing the serial connection and set home coordinates """
        self.go_home()


    def auto_detect_serial_unix(self, preferred_list=['*']):
        '''try to auto-detect serial ports on posix based OS'''
        import glob
        glist = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        ret = []

        # try preferred ones first
        for d in glist:
            for preferred in preferred_list:
                if fnmatch.fnmatch(d, preferred):
                    #ret.append(SerialPort(d))
                    ret.append(d)
        if len(ret) > 0:
            return ret
        # now the rest
        for d in glist:
            #ret.append(SerialPort(d))
            ret.append(d)
        return ret

    def go_home(self, offset_x=0, offset_y=0):
        self.is_moving = True
        if not self.is_serial_open:
            self.serialport = serial.Serial(self.port, self.baudrate )
            self.is_serial_open = True
        else:
            print("Reopening the connection")
            self.serialport.close()
            time.sleep(4)
            self.serialport = serial.Serial(self.port, self.baudrate )
            
        self.location = [0,0]
            
        # HOMING
        # #FF#09#5A#A5
        self.send_CMD(9, 90, 165)
        # #FF#AA#08#01#01#5A#A5#55
        self.send_CMD_array([170, 8, 1, 1, 90, 165, 85])
        time.sleep(5)
        self.is_moving = False
        self.set_speed(self.speed)

    def getcurrentpos(self):
        # retrieve the latest position in the stack        
        return (self.currentposition[0], self.currentposition[1], self.currentposition[2])        
      
    def move_rel(self, position=(0,0,0), wait_until_done=False):
        # check if stage is moving or not
        self.go_to(position[0], position[1], position[2], 'rel')
        return ""

    def move_abs(self, position=(0,0,0), wait_until_done=False):
        self.go_to(position[0], position[1], position[2], 'abs')
        return ""

    def zero_position(self):
        self.currentposition = (0,0,0)


    def go_to(self, pos_x=0, pos_y=0, pos_z=0, mode='abs'):
        # trigger a motion event
		
        pos_x_c = self.currentposition[0]
        pos_y_c = self.currentposition[1]
        pos_z_c = self.currentposition[2]

        if mode == 'abs':
            pos_z = pos_z - pos_z_c
		
        elif mode == 'rel':
            if self.is_debug: print("To Go: X/Y/Z: "+str(pos_x)+"/"+str(pos_y)+"/"+str(pos_z))            
            pos_x = pos_x_c+pos_x
            pos_y = pos_y_c+pos_y


        pos_x = int(pos_x)
        pos_y = int(pos_y)
        pos_z = int(pos_z)
        if self.is_debug: print("X/Y/Z:"+str(pos_x)+"/"+str(pos_y)+"/"+str(pos_z))
        if self.is_debug: print("cX/cY:"+str(pos_x_c)+"/"+str(pos_y_c)+"/"+str(pos_z_c))		
		
        if pos_x > 1650:
            pos_x = 1650
        if pos_y > 1650:
            pos_y = 1650
        if pos_x < 0:
            pos_x = 0
        if pos_y < 0:
            pos_y = 0

        self.currentposition = [pos_x,pos_y,pos_z_c+pos_z]

        self.is_moving = True
        diff_x, diff_y = pos_x-pos_x_c,pos_y-pos_y_c
        pos_x+=100
        self.set_speed(self.speed) # not sure if we need to recall that all the time?
        self.send_CMD_array([
            170, 16, 5, 1, 80, 1,
            int(pos_x // 256), int(pos_x % 256),
            int(pos_y // 256), int(pos_y % 256),
            0, 0, 0, 0, 85])
        
        # make sure the z-motor runs and we don't wait twice 
        time_tmp = time.time()
        # z-stage is always in relative mode! 
        self.motor_z.rotate(pos_z, nofork=True)
        
        time_sleep = (abs(diff_x)+abs(diff_y))/600
        if self.is_debug: print("I need to wait: "+str(time_sleep) + "s")
        try:
            time.sleep(time_sleep-(time.time()-time_tmp))
        except:
            pass # in case we waited long enough already

        self.is_moving = False

    def send_CMD(self, D1, D2, D3):
        buffer = bytes([255, D1, D2, D3])
        if self.is_debug: print("send", buffer)
        self.serialport.write(buffer)
        self.serialport.flush()

    def send_CMD_array(self, arr):
        if self.is_debug: print("send", arr)
        buffer = bytes([255]+arr)
        if self.is_debug: print("send", buffer)
        self.serialport.write(buffer)
        self.serialport.flush()

    def set_speed(self, speed):
        # speed has to be between 1..4
        # Setting burning time/laser power/brightness/tilt detection/motor speed
        print("Setting speed to: "+str(speed))
        self.send_CMD_array([170,13,3,3,10,20,15,2,int(speed),0,0,85])

    def set_laser_intensity(self, intensity):
        pass

    def set_led(self, state=1):
        pass