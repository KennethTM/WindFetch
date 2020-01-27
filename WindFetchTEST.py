#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 14:23:53 2019

@author: kenneth
"""

import numpy as np
import rasterio
from matplotlib import pyplot as plt
#import timeit

test = '/home/kenneth/Documents/WindFetch/test/lake_test.tif'

with rasterio.open(test) as ds_in:
    arr_in = ds_in.read(1).astype("float")
    meta_in = ds_in.profile
    resolution = ds_in.res[0]
    nrow, ncol = arr_in.shape
    
arr_in[arr_in != 1] = np.nan

arr_in[arr_in == 1] = -1

#todo: timing mellem at acces values i np.array vs python list

def fetch_length(array, resolution):
    
    nrow, ncol = array.shape
    #fetch = np.full(ncol, np.nan) #-1*resolution
    fetch = [np.nan]*ncol
    
    list_fetch = []
    
    for row in range(nrow):
        
        land = array[row]
        
        for col in range(ncol):
            
            if np.isnan(land[col]):
                fetch[col] = 0
            else:
                if fetch[col] >= 0:
                    fetch[col] = fetch[col] + resolution
                else:
                    fetch[col] = fetch[col] - resolution
                        
        list_fetch.append(list(fetch))
            
    return(np.array(list_fetch))
    
    
plt.imshow(arr_in) 
plt.imshow(fetch_length(arr_in, resolution)) 








#cython??
#set up standard test
#http://nealhughes.net/cython1/

def fetch_length(double[:,:] array, double resolution):
    
    cdef int nrow = array.shape[0]
    cdef int ncol = array.shape[1]
    
    cdef double[:] fetch = np.zeros (ncol)
    
    #nrow, ncol = array.shape
    #fetch = np.full(ncol, np.nan) #-1*resolution
    #fetch = [np.nan]*ncol
    
    list_fetch = []
    
    for row in range(nrow):
        
        land = array[row]
        
        for col in range(ncol):
            
            if np.isnan(land[col]):
                fetch[col] = 0
            else:
                if fetch[col] >= 0:
                    fetch[col] = fetch[col] + resolution
                else:
                    fetch[col] = fetch[col] - resolution
                        
        list_fetch.append(list(fetch))
            
    return(np.array(list_fetch))