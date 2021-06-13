import serial
import time
import time, datetime, os
import xyz_stepper as xy

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  8 13:58:10 2021

@author: bene
"""

import tifffile as tif 
import numpy as np
import NanoImagingPack as nip
import matplotlib.pyplot as plt
#%%
filename = '2021_06_02-Antibody_AF647_Microtubule_HeLa_STACK.tif'
image_stack = tif.imread(filename)
background = np.mean(image_stack[20:,:,:],0)



#%%
i_slice = 22
threshold = 0
blurkernel = 2

background_blur = nip.gaussf(background,blurkernel)

myimage_raw=image_stack[i_slice,:,:]
myimage = myimage_raw/background_blur
myimage /= np.max(myimage)
myimage[myimage<threshold]=0
plt.subplot(221)
plt.title('CLEANED')
plt.imshow(myimage, cmap='gray')
plt.subplot(222)
plt.title('BACKGROUND')
plt.imshow(background_blur,cmap='gray')
plt.subplot(223)
plt.title('RAW')
plt.imshow(myimage_raw,cmap='gray')


tif.imsave(filename+"_sub.tif", myimage)