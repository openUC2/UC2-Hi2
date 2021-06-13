# -*- coding: utf-8 -*-
"""
Created on Fri Jun 11 12:13:29 2021

@author: UC2
"""

# -*- coding: utf-8 -*-
"""
Created on Mon Jun  7 17:47:46 2021

@author: UC2
"""

# organize the imports
try:
    import opentrons.execute
    from opentrons import types 
    from  opentrons.types import Location, Point
    
    from imjoy_rpc import connect_to_server
    
    import nest_asyncio
    nest_asyncio.apply()
    import asyncio
except:
    print("Debugging")
    
    class Microscope :
        def __init__(self):
            print("Initiliaztion")
            self.position = {}
            self.position["x"]=0
            self.position["y"]=0
            self.position["z"]=0
            
   
        def move(self, blocking=True, absolute=True):
            pass

        def autofocus_coarse(self,dz=1, nz=1, is_uselight=True):
            return 1
        def autofocus_fine(self,dz=1, nz=1, is_uselight=True):
            return 1
        def autofocus_fast(self,dz=1, nz=1, is_uselight=True):
            return 1
        def set_laser_led(self, I_laser, I_led):
            pass
        def capture_image_to_disk(self, params ):
            pass

    
import time
import numpy as np




class ImJoyProcessor:
    '''
    #example

    serverip="http://21.3.2.2"
    workspace = "b796e6f7-f670-40bc-936b-fa6907a4e733"
    token = "imjoy@eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZXMiOlsiYjc5NmU2ZjctZjY3MC00MGJjLTkzNmItZmE2OTA3YTRlNzMzIl0sImV4cGlyZXNfYXQiOm51bGwsInVzZXJfaWQiOiIzODAzNWZiZC1kMTcyLTQ3ZWItOWFhZS0yNGFkOGI0YTZhMGQiLCJwYXJlbnQiOiJiNzk2ZTZmNy1mNjcwLTQwYmMtOTM2Yi1mYTY5MDdhNGU3MzMiLCJlbWFpbCI6bnVsbCwicm9sZXMiOltdfQ.0ew2D31EfIYM2amUJBDCATLKH9SLSiQxFU4Nz7spbOs"
    pluginname = 'localization'

    IJP = ImJoyProcessor(serverip,  workspace, token, pluginname)
    IJP.request_connect()

    for i in range(3):
        image = 1.*(np.abs(np.random.randn(100,100))>.9999)
        print(np.sum(image))
        IJP.request_result(image)
    '''

    def __init__(self, serverip, workspace, token, pluginname):
        self.serverip = serverip
        self.workspace = workspace
        self.token = token
        self.loop = asyncio.get_event_loop()
        self.image = None
        self.pluginname = pluginname
        self.return_result = -1
        
    async def connect_to_server(self):
        self.ws = await connect_to_server(server_url=self.serverip+":9527", 
                               workspace=self.workspace, 
                               token=self.token)
        print("WS")
        print(self.ws)
        self.plugin = await self.ws.getPlugin(self.pluginname)
        
    def request_connect(self):
        self.loop.run_until_complete(self.connect_to_server())
        
        
    async def run_plugin(self):
        self.return_result = await self.plugin.localize(self.image)
        
    def request_result(self,image):
        self.image = image
        self.loop.run_until_complete(self.run_plugin())
        return self.return_result
    





def move_to_coord(pipette, position_xyz, offset = (0,0,0), minimum_z_height=190):
    if pipette._last_tip_picked_up_from is None:
        print("Please add a pipette first!")
        
        
    position_final = (position_xyz[0]+offset[0],
                        position_xyz[1]+offset[1],
                        position_xyz[2]+offset[2])
    print("Moving to: "+str(position_final))                       
    pipette.move_to(Location(Point(*position_final), None),minimum_z_height=minimum_z_height)

   
def pickup_fresh_pipette_tip(i_pipette: int, pipette, tiprack, offset_pipette_rack):
    
    # check if pipette is attached
    try:
        if pipette._last_tip_picked_up_from is not None:
            pipette.drop_tip()
    except:
        print("Something went wrong")
    my_fresh_tip = tiprack.wells()[i_pipette]
    adjusted_location = my_fresh_tip.center().move(types.Point(x=offset_pipette_rack[0], y=offset_pipette_rack[1], z=offset_pipette_rack[2]))
    #_pipette.pick_up_tip(_adjusted_location)
    #pipette.move_to(_adjusted_location)
    try:
        pipette.pick_up_tip(adjusted_location)
    except:
        pipette.drop_tip()
        pipette.pick_up_tip(adjusted_location)
    
    print("My pipette number: "+str(i_pipette)+"and type: "+str(type(i_pipette)))
    return i_pipette + 1

def takesnapshot(pipette, position_sample_light, offset=(2,-2,0), I_led=1, I_laser=0):
    microscope.set_laser_led(I_laser,I_led)
    move_to_coord(pipette, position_sample_light, offset=offset, minimum_z_height=minimum_z_height)
    microscope.capture_image_to_disk()
    microscope.set_laser_led(0,0)
    
def process_image(image, workspace, token, serverip):
    '''
    Connect to ImJoy and test the plugins functionality 

    serverip="http://21.3.2.2"
    workspace = "b796e6f7-f670-40bc-936b-fa6907a4e733"
    token = "imjoy@eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzY29wZXMiOlsiYjc5NmU2ZjctZjY3MC00MGJjLTkzNmItZmE2OTA3YTRlNzMzIl0sImV4cGlyZXNfYXQiOm51bGwsInVzZXJfaWQiOiIzODAzNWZiZC1kMTcyLTQ3ZWItOWFhZS0yNGFkOGI0YTZhMGQiLCJwYXJlbnQiOiJiNzk2ZTZmNy1mNjcwLTQwYmMtOTM2Yi1mYTY5MDdhNGU3MzMiLCJlbWFpbCI6bnVsbCwicm9sZXMiOltdfQ.0ew2D31EfIYM2amUJBDCATLKH9SLSiQxFU4Nz7spbOs"
    for i in range(3):
        image = np.abs(np.random.randn(200,200))
        locations = process_image(image, workspace, token, serverip)
        print(locations)
    '''

    loop = asyncio.get_event_loop()
    async def run_plugin():
        global locations
        locations = -1
        ws = await connect_to_server(server_url=serverip+":9527", 
                               workspace=workspace, 
                               token=token)
        localize_plugin = await ws.getPlugin("localization")
        locations = await localize_plugin.localize(image)
    #loop.run_until_complete(run_plugin())
    loop.run_until_complete(run_plugin())
    print("number of cells in well 2: "+str(locations))
    return locations
    
    


def wellscan(microscope, offset_x, offset_y, i_experiment,
        Nx=3, Ny=3, well_to_well_steps = 9000,
        autofocus_dz=2000, autofocus_Nz=11,
            name_experiment="wellscan_",
            focus_pos_list=None,
            is_autofocus=True, is_autofocus_fine = False,
            is_autofocus_fast = False,
            I_laser=0, I_led=1,
            t_debounce=.5,
            is_find_prefocus=False,
            process_func=None,
            is_meander=False):
    """
    
    offset_x, offset_y:
        These values represent the positio of the zero-position for the A1 locatoin in a 96 well plate 
       
    Save a set of images in a wellscan

    Args:
        microscope: Microscope object
        offset_x (int): Number of images to take
        offset_y (int/float): Time, in seconds, between sequential captures
    """
    folder = "wellscan_"

    # cast variables
    xyz_fit_func = None # this is the fitted function for a global tilted plane
    Nx = int(Nx)
    Ny = int(Ny)
    well_to_well_steps = int(well_to_well_steps)

    # get current z-position for the stage
    offset_z = microscope.position["z"]

    # move to the home positoin
    print("Start moving to the position")

    # go to the first location
    microscope.move((offset_x,offset_y,offset_z), absolute=True)

    # in case we have focus positions available, skip it
    print("Start scan")
    #%%
    if focus_pos_list is None:
        focus_pos_list = []
        
    if is_find_prefocus:
        focus_pos_list_pre, location_list, xyz_fit_func = gen_focus_pos_list(microscope,Nx-3,Ny-3,offset_x,offset_y,well_to_well_steps, autofocus_dz, autofocus_Nz)

    process_val_list = []

    # preset variables
    i_image = 0
    i_well = 0
    last_offset_z_row = offset_z
    for wellpos_y in range(Ny):
        for wellpos_x in range(Nx):
            if is_meander: 
                if wellpos_y%2==0  :
                    wellpos_x=Nx-wellpos_x-1

            
            if last_offset_z_row == 0:
                offset_z = last_offset_z_row
            current_x = offset_x+well_to_well_steps*wellpos_x
            current_y = offset_y+well_to_well_steps*wellpos_y
            print("Move microscope to (XY): "+str(current_x)+"/"+str(current_y))

            if is_autofocus:
                if is_find_prefocus:
                    offset_z =  xyz_fit_func[0]*current_x+xyz_fit_func[1]*current_y+xyz_fit_func[2] 
                    is_autofocus_fine = True
                    
                microscope.move((current_x, current_y, offset_z), absolute=True, blocking=True)

                # turn on laser/led and perform autofocus
                microscope.set_laser_led(I_laser,I_laser)
                print("ERROR make sure the correct laser itnensity is assigned!")
                if is_autofocus_fast:
                    offset_z = microscope.autofocus_fast(autofocus_dz)
                elif is_autofocus_fine:
                    # turn on laser/led and perform autofocus
                    offset_z = microscope.autofocus_coarse(dz=300, nz=3, is_uselight=True)
                else:
                    offset_z = microscope.autofocus_coarse(dz=autofocus_dz, nz=autofocus_Nz, is_uselight=True)
                microscope.set_laser_led(0,0)                
                
                # append the values to the list
                focus_pos_list.append(offset_z)

                if last_offset_z_row == 0:
                    last_offset_z_row = offset_z
            else:
                if is_find_prefocus:
                    offset_z = xyz_fit_func[0]*current_x + xyz_fit_func[1]*current_x + xyz_fit_func[2]
                else:
                    try:
                        offset_z = focus_pos_list[i_well]
                    except Exception as e:
                        print(str(e))
                        offset_z = microscope.position["z"]
                microscope.move((current_x, current_y, offset_z), absolute=True, blocking=True)

            # debounce
            time.sleep(t_debounce)

            # turn on light and take an image
            if I_laser > 0:
                params = {
                    "use_video_port": True,
                    "bayer": False,
                    "temporary" :False,
                    "filename": name_experiment+"FLOU_"+
                                str("%04d" % i_experiment)+"_"+
                                str("%04d" % i_well)+"_"+
                                str("%04d" % i_image)+"_"+
                                str(wellpos_x)+"_"+str(wellpos_y),
                }
                microscope.set_laser_led(0,1)
                time.sleep(.5)
                microscope.capture_image_to_disk(params)
            if I_led > 0:
                params = {
                    "use_video_port": True,
                    "bayer": False,
                    "temporary" :False,
                    "filename": name_experiment+"BF_"+
                                str("%04d" % i_experiment)+"_"+
                                str("%04d" % i_well)+"_"+
                                str("%04d" % i_image)+"_"+
                                str(wellpos_x)+"_"+str(wellpos_y),
                }
                microscope.set_laser_led(0,0)
                time.sleep(.5)
                microscope.capture_image_to_disk(params)

            if process_func is not None:
                image = microscope.grab_image_np()[550:650,550:650] # np.ones((100,100))
                proc_return = process_func(image)
                print("Proc Value: "+str(n_cells))
                process_val_list.append((proc_return, current_x, current_y, offset_z))

            if not I_laser and not I_led:
                raise Exception
            microscope.set_laser_led(0,0)
            i_image += 1
            i_well += 1

    i_experiment += 1

    if process:
        return focus_pos_list, process_val_list
    else:
        return focus_pos_list

    
def move_to_well(microscope, offset_x, offset_y, offset_z=None, well_index=0, well_to_well_steps=9000):
    '''
    Move the microscope lens to a well with an ID following the namin convention of the opentron API
    
    offset_x, offset_y:
        this is the zero position for the 0th well 
    '''
    if offset_z is None:
        offset_z = microscope.position["z"]

    # convet the list coordinates into x/y coordinates
    wellposlist_final = wellid_to_xy(well_index)[0]
    posx, posy = wellposlist_final[0], wellposlist_final[1]
    current_x = offset_x+(well_to_well_steps*posx)
    current_y = offset_y+well_to_well_steps*posy
    
    print("Moving to well location:" + str(well_index)+"at: "+str(posx)+"/"+str(posy)+"/"+str(well_to_well_steps))
    print("At Location:", str(current_x), str(current_y), str(offset_z))
    
    # compeensate the backlash
    microscope.move((current_x,current_y,offset_z-100),absolute=True)
    microscope.move((current_x,current_y,offset_z),absolute=True)
    
   
def wellid_to_xy(well_id_list, N_wells = 96, Nx=8, Ny=12):
   '''
   convert the list of individual well ids in wellposlist into xy coordinates
   
   example:
       well_id_list = np.arange(0,10)
       wellposlist_final ,_= wellpos_to_xy(well_id_list)
   '''
   # convet the list coordinates into x/y coordinates
   well_indices = np.zeros((Nx, Ny))
   i_index=0
   for iy in range(Ny):
        for ix in (Nx-1-np.arange(Nx)):
            well_indices[ix, iy]=i_index
            i_index+=1
            
   wellposlist_final = []
   try:
       for ipos in well_id_list:
           posx, posy = np.where(ipos==well_indices)
           wellposlist_final.append((posx,posy))
       wellposlist_final = np.squeeze(np.array(wellposlist_final))
   except:
       posx, posy = np.where(well_id_list==well_indices)
       wellposlist_final = np.array((posx,posy))
   return wellposlist_final, well_indices


def wellxy_to_id(well_xy_list, N_wells = 96, Nx=8, Ny=12):
    '''
   convert the list of individual well ids in wellposlist into xy coordinates
   
   example:
       well_xy_list = (4,2)
       wellposlist_final ,_= wellxy_to_id(well_xy)
    '''
    well_xy_list = np.squeeze(np.array(well_xy_list))
    # convet the list coordinates into x/y coordinates
    well_pos_list = []
    for iy in range(12):
        for ix in (Nx-1-np.arange(Nx)):
            well_pos_list.append((ix,iy))

    try:
        well_id_list_final = []
        for ipos in range(well_xy_list.shape[0]):
            well_id = np.where(np.mean(np.squeeze(np.array(well_pos_list))==well_xy_list[ipos,:],-1)==1)
            well_id_list_final.append(well_id)
        well_id_list_final = np.squeeze(np.array(well_id_list_final))
    except:
        well_id_list_final = np.where(np.mean(np.squeeze(np.array(well_pos_list))==well_xy_list,-1)==1)
           
    return well_id_list_final, well_pos_list

def wellscan_list(microscope, offset_x, offset_y, i_experiment,
        well_id_list, well_to_well_steps = 9000,
        autofocus_dz=2000, autofocus_Nz=11,
            name_experiment="wellscan_",
            focus_pos_list=None,
            is_autofocus=True, is_autofocus_fine = False,
            is_autofocus_fast = False,
            I_laser=0, I_led=1,
            t_debounce=.5,
            is_find_prefocus=False,
            process_func=None):
    """
    
    offset_x, offset_y:
        These values represent the positio of the zero-position for the A1 locatoin in a 96 well plate 
        
    wellposlist:
        The list contains all the well you would like to image e.g. wellposlist = (0,1,55) - it follows opentrons naming conventoin
        
       
    Save a set of images in a wellscan

    Args:
        microscope: Microscope object
        offset_x (int): Number of images to take
        offset_y (int/float): Time, in seconds, between sequential captures
    """
    
    # cast variables
    xyz_fit_func = None # this is the fitted function for a global tilted plane
    well_to_well_steps = int(well_to_well_steps)

    # in case we have focus positions available, skip it
    print("Start scan")
    #%%

    # convert the list of indices to xy coordinates
    wellposlist_final, well_indices = wellid_to_xy(well_id_list)
    
    if is_find_prefocus:
        # get the locations which are the most far away from the plate center (i.e. corners)
        calib_pos = ((np.min(wellposlist_final[:,0]),np.min(wellposlist_final[:,1])),
                     (np.max(wellposlist_final[:,0]),np.min(wellposlist_final[:,1])), 
                     (np.max(wellposlist_final[:,0]),np.max(wellposlist_final[:,1])),       
                     (np.min(wellposlist_final[:,0]),np.max(wellposlist_final[:,1])))
        # convert the well positions into IDs
        calib_ids = wellxy_to_id(calib_pos)[0]
        # estimate the tilted plane from the 4 coordinates
        focus_pos_list_pre, location_list, xyz_fit_func = gen_focus_pos_list(microscope, calib_well_ids=calib_ids, 
                                                                             offset_x=offset_x, offset_y=offset_y,
                                                                             well_to_well_steps=well_to_well_steps,
                                                                             autofocus_dz=autofocus_dz, autofocus_Nz=autofocus_Nz)

    if focus_pos_list is None or is_find_prefocus or is_autofocus:
        focus_pos_list = []

    process_val_list = []

    # preset variablesautofocus_coarse
    i_image = 0
    i_well = 0
    for wellpos_xy in wellposlist_final:        
        current_x = wellpos_xy[0]
        current_y = wellpos_xy[1]
        
        if is_autofocus:
            if is_find_prefocus:
                offset_z = xyz_fit_func[0]*(current_x*well_to_well_steps) + xyz_fit_func[1]*current_y*well_to_well_steps +                             xyz_fit_func[2] 
                    
                is_autofocus = True
                
            # move to well
            move_to_well(microscope, offset_x=offset_x, offset_y=offset_y, offset_z=offset_z, well_index=wellxy_to_id(wellpos_xy)[0], well_to_well_steps=well_to_well_steps)
            
            
            # turn on laser/led and perform autofocus
            microscope.set_laser_led(I_laser,I_laser)
            print("ERROR make sure the correct laser itnensity is assigned!")
            if is_autofocus_fast:
                offset_z = microscope.autofocus_fast(autofocus_dz)
            elif is_autofocus_fine:
                # turn on laser/led and perform autofocus
                offset_z = microscope.autofocus_coarse(dz=500, nz=5, is_uselight=True)
            else:
                offset_z = microscope.autofocus_coarse(dz=autofocus_dz, nz=autofocus_Nz, is_uselight=True)
            microscope.set_laser_led(0,0)                

            # append the values to the list
            focus_pos_list.append(offset_z)

        else:
            if is_find_prefocus:
                offset_z =  xyz_fit_func[0]*(current_x*well_to_well_steps)+xyz_fit_func[1]*current_y*well_to_well_steps+xyz_fit_func[2] 
                focus_pos_list.append(offset_z)
            else:
                try:
                    offset_z = focus_pos_list[i_well]
                except Exception as e:
                    print(str(e))
                    offset_z = microscope.position["z"]
            
            # move to well
            move_to_well(microscope, offset_x, offset_y, offset_z, well_index=wellxy_to_id(wellpos_xy)[0], well_to_well_steps=well_to_well_steps)
            
        print("offset_z:"+str(offset_z))

        # debounce
        time.sleep(t_debounce)

        # turn on light and take an image
        if I_laser > 0:
            params = {
                "use_video_port": True,
                "bayer": False,
                "temporary" :False,
                "filename": name_experiment+"FLOU_"+
                            str("%04d" % i_experiment)+"_"+
                            str("%04d" % i_well)+"_"+
                            str("%04d" % i_image)+"_"+
                            str(current_x)+"_"+str(current_y),
            }
            microscope.set_laser_led(0,1)
            time.sleep(.5)
            microscope.capture_image_to_disk(params)
        if I_led > 0:
            params = {
                "use_video_port": True,
                "bayer": False,
                "temporary" :False,
                "filename": name_experiment+"BF_"+
                            str("%04d" % i_experiment)+"_"+
                            str("%04d" % i_well)+"_"+
                            str("%04d" % i_image)+"_"+
                            str(current_x)+"_"+str(current_y),
            }
            microscope.set_laser_led(0,0)
            time.sleep(.5)
            microscope.capture_image_to_disk(params)

        if process_func is not None:
            image = microscope.grab_image_np()[550:650,550:650] # np.ones((100,100))
            proc_return = process_func(image)
            print("Proc Value: "+str(proc_return))
            process_val_list.append((proc_return, current_x, current_y, offset_z))

        if not I_laser and not I_led:
            raise Exception
        microscope.set_laser_led(0,0)
        i_image += 1
        i_well += 1

    i_experiment += 1

    if process_func is not None:
        return focus_pos_list, process_val_list
    else:
        return focus_pos_list
    
    
def gen_focus_pos_list(microscope,offset_x, offset_y, well_to_well_steps=9000,
                       calib_well_ids=None, autofocus_dz=200, autofocus_Nz=9):
    '''
    simple function to compute a tilted plane based on 4 focus positions
    
    Returning c: 
    cx = 9000
    cy = 2*9000
    Z = C[0]*cx + C[1]*cy + C[2]
    '''
    print("Trying to estimate the focus positions")
    

    location_list = []
    for wellpos in list(calib_well_ids):
        print(wellpos)
        move_to_well(microscope, offset_x = offset_x, offset_y=offset_y, well_index=wellpos, well_to_well_steps=well_to_well_steps)
            
        #microscope.move(c_pos, absolute=True, blocking=True)
        offset_z = microscope.autofocus_coarse(dz=autofocus_dz, nz=autofocus_Nz, is_uselight=True)
        pos_xyz = microscope.position
        location_list.append((pos_xyz['x'],pos_xyz['y'],offset_z))
        print("Location for gen poslist: ",str((pos_xyz['x'],pos_xyz['y'],offset_z)))
        
    data = np.array(location_list)

    
    # regular grid covering the domain of the data
    X,Y = np.meshgrid(np.arange(np.min(data[:,0]), np.max(data[:,0]), well_to_well_steps), np.arange(np.min(data[:,1]), np.max(data[:,1]), well_to_well_steps))

    # best-fit linear plane
    A = np.c_[data[:,0], data[:,1], np.ones(data.shape[0])]
    C,_,_,_ = np.linalg.lstsq(A, data[:,2])    # coefficients

    # evaluate it on grid
    focus_pos_list  = C[0]*X + C[1]*Y + C[2]
    
    return focus_pos_list, location_list, C



if __name__ == "__main__":
    # genrate fake microscope
    microscope = Microscope()

    offset_x = 66000
    offset_y = 1000
    
    num_cell_list = []
    autofocus_dz = 2000
    autofocus_Nz= 15
    mytime = -time.time()
    #t_duration = 20 # minutes
    focus_pos_list = None # start with a fresh list
    well_to_well_steps= 9000
    t_duration = 60 # how long does the experiment preform?
    t_period = 5 # min - how often should the expimrent be carried out?
    is_autofocus = False
    is_find_prefocus = True
        
    i_experiment = 0
    
    print(i_experiment)
    timestamp = str( 0)
    
    wellposlist = np.arange(0,32)
    wellposlist = (7,0,24,31)
    
    wellid_to_xy(wellposlist)
    # perform a testing well scan by moving robot to light position and do a whole plate scan
    #move_to_coord(pipette_8, position_sample_light, offset=(0,0,0), minimum_z_height=minimum_z_height)
    focus_pos_list = wellscan_list(microscope, 
            offset_x, 
            offset_y, 
            i_experiment,wellposlist,
            well_to_well_steps,
            autofocus_dz, 
            autofocus_Nz,
            name_experiment="wellscan_post_2_"+timestamp,
            focus_pos_list=focus_pos_list, 
            is_find_prefocus=is_find_prefocus,
            is_autofocus=is_autofocus,
            is_autofocus_fine = False, 
            is_autofocus_fast = False,
            I_laser=0, I_led=1,
            t_debounce=0.5)
    
    
    
    