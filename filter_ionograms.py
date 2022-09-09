#!/usr/bin/env python3

# Save files in each of the folders using pickle (multi-frequency) and later load the files to make the plots through another script.
# The filter can be further improved  - with little more complex approaches so that it gets close to perfect. The current filter - isn't perfect
# and sometimes select files which don't seem to be from the transmitter station we are looking the signals from. This could be due to -- (i) loss
# of gps lock or other technical issues, (ii) imperfect algorithm which we have now ! 

## 

import pickle
from numpy import unravel_index
import datetime
import shutil
import time
import sys
import scipy.constants as c
import h5py
import numpy as n

import glob
import os

import matplotlib.pyplot as plt
import pandas as pd
import ipdb


# Folder which has lfm files. 
rootdir = '/media/kc3pve/Seagate Backup Plus Drive/chirp'


# All folders (within the rootdir) named by days of the calendar which has the lfm_files
dirs = sorted(os.listdir(rootdir))

# Remove first three undated folders. So, dirs has only dated folders which contain lfm files. The rootdir will vary by where the data is stored. And, dirs may need to be tweaked to ensure 
# it is taking only into the 'dated-folders'.  
#dirs = dirs[3:-1]

# folder where I want to save my data
output_dir1 = "/home/kc3pve/Downloads/chirp_juha2b/Plots20"

freqlist = [60, 80, 100, 120, 140, 160] 


def k_largest_index_argsort(S, k):
    idx = n.argsort(S.ravel())[:-k-1:-1]
    return n.column_stack(n.unravel_index(idx, S.shape))


def filter_ionograms(f, Datadict, normalize_by_frequency=True):
    ho = h5py.File(f, "r")
    t0 = float(n.copy(ho[("t0")]))
    
    if not "id" in ho.keys():
        return
    cid = int(n.copy(ho[("id")]))  # ionosonde id
   
    out_dir1 = os.path.join(output_dir1, dirs1)

    # Create new output directory
    if not os.path.exists(out_dir1):
        os.makedirs(out_dir1)

    #print("Reading %s rate %1.2f (kHz/s) t0 %1.5f (unix)" % (f, float(n.copy(ho[("rate")]))/1e3, float(n.copy(ho[("t0")]))))
    S = n.copy(ho[("S")])          # ionogram frequency-range
    freqs = n.copy(ho[("freqs")])  # frequency bins
    ranges = n.copy(ho[("ranges")])  # range gates
    Rate = n.copy(ho[("rate")])/1000  # Rate
    
    DataDict["freqs"] = freqs
   
    if normalize_by_frequency:
        for i in range(S.shape[0]):
            #noise = n.nanmedian(S[i, :])
            noise = n.median(S[i, :])
            #print('i=%d' %(i)) 
            if noise !=	0: 
                S[i, :] = (S[i, :]-noise)/noise
                                   
        S[S <= 0.0] = 1e-3

    max_range_idx = n.argmax(n.max(S, axis=0))
    # axis 0 is the direction along the rows but max_range_idx gives maximum index along ranges
        
    unarg = unravel_index(S.argmax(),S.shape)
    
    dB = n.transpose(10.0*n.log10(S))
    if normalize_by_frequency == False:
        dB = dB-n.nanmedian(dB)
    
    unarg1 = unravel_index(n.nanargmax(dB),dB.shape)
    
    # Assume that t0 is at the start of a standard unix second therefore, the propagation time is anything added to a full second

    dt = (t0-n.floor(t0))
    dr = dt*c.c/1e3    
    range_gates = dr+2*ranges/1e3
    r0 = range_gates[max_range_idx]
    # r0 is range at which the SNR maximum occurs along the range_gates
    
    DataDict["range_gates"] = range_gates
    
    dBB = {}
    for freq in freqlist:
        dBB[freqs[freq]/1e6] = dB[:, freq]
        
    #ipdb.set_trace()
    
    #  I am trying to find positions in dB where positive dB values [for the frequency for which the maximum in dB has occurred] 
    #  are greater than a threshold [the threshold being : am - 3*ast]
    dB1a = dB[:,unarg1[1]]
    dB2 = dB1a[dB1a>0]
    pos = n.argwhere(dB1a > 0)
    rg_2 = range_gates[pos]
    ast = n.std(dB2)
    if len(dB2) == 0:
        print('No useful data')     
        return

    am = n.max(dB2)
    apos = n.argwhere(dB2 > (am -3*ast))
    rg_3 = rg_2[apos]

    arr = []
    for j in rg_3:
            arr.append(j[0][0])
            
    arr1 = n.array(arr)            
    pos1 = n.argwhere((arr1 > 400) & (arr1 < 1000))
       
    ch1 = DataDict['ch1']
   
    if ((Rate == 100) and (400 < r0 < 1000)) |((Rate == 100) and (1000 < r0 < 1500) and (len(pos1) > 0)) :
        print('yes')

        #if jf == 534:

        #if range_gates.shape[0] == DataDict['range_gates2'].shape[0]:
        #    range_gates2 = range_gates
        #    DataDict['range_gates2'] = range_gates
        #else:  
        #    range_gates2 = DataDict['range_gates2']
        #    DataDict['range_gates2'] = DataDict['range_gates2']
    
        ch1 += 1
        if ch1 == 1:
            
            DB3 = {}
            for freq in freqlist:
               DB3[freqs[freq]/1e6]  = dBB[freqs[freq]/1e6]
  
            T01 = n.array([t0])
            T03 = T01
            range_gates3 = range_gates
            DataDict['range_gates2'] = range_gates   
            
        else:
           
            DB3 = {}
            for freq in freqlist:
                # This try-except is tried as - very occassionally - the first option fails because of mismatch of dimensions of the variables being 
                # sought to be column_stacked. In that case, for this particular file, nans are padded to the the second variable to match 
                # the equivalent dimension of the first variable. This might need little more work if this situation arises for the first file for a given day ! And it will also need  
                # more work if the second variable is greater than the first variable [the reverse is assumed as this situation has occured only for one day so far I think] !  
                try:
                    DB3[freqs[freq]/1e6]  = n.column_stack((DataDict['DBall'][freqs[freq]/1e6], dBB[freqs[freq]/1e6]))
                except:
                    dtest = n.full([DataDict['DBall'][freqs[freq]/1e6].shape[0] - dBB[3].shape[0]],None)
                    dtest[:] = n.NaN
                    dtest = n.concatenate((dBB[freqs[freq]/1e6],dtest),axis=None)
                    DB3[freqs[freq]/1e6]  = n.column_stack((DataDict['DBall'][freqs[freq]/1e6], dtest))
           
            	
            T03  = n.hstack((DataDict['Time'], n.array([t0])))
            try:
                range_gates3 = n.column_stack((DataDict['range_gates3'],range_gates))
                DataDict['range_gates2'] = range_gates
            except:
                range_gatestest = n.full(DataDict['range_gates3'].shape[0] - range_gates.shape[0], None)
                range_gatestest[:] = n.NaN
                range_gatestest = n.concatenate((range_gates,range_gatestest),axis = None)
                range_gates3 = n.column_stack((DataDict['range_gates3'],range_gatestest))
                DataDict['range_gates2'] = range_gatestest
                                                       
        DataDict['DBall'] = DB3
        DataDict['Time'] = T03
        DataDict['range_gates3'] = range_gates3
        DataDict['ch1'] = ch1
        print('ch1_inside=%d' %(ch1))

def save_var(DataDict):

    path1 = output_dir1 + '/' + dirs1 + '/' + dirs1[5:10] + 'k.data'
    print(path1)
    #ipdb.set_trace()
    with open(path1, 'wb') as f:
        pickle.dump(DataDict, f)


if __name__ == "__main__":

        for j in range(0, len(dirs)):
            dirs1 = dirs[j]
            
            dtt1 = datetime.datetime.strptime('2021-09-09','%Y-%m-%d').date()
            dtt2 = datetime.datetime.strptime(dirs1[0:10],'%Y-%m-%d').date()

            # Looking to process data after certain date:
            if dtt2 > dtt1 :
            
            # Looking to process data for a certain day:
            #if dirs1[0:10] == '2021-08-07':
            
            # Looking to process data for all days for the year of choice : [e.g.: 2021]
            # if dirs1[0:4] == '2021':
                
                # path goes into each-day-folder within the rootdir 
                path = os.path.join(rootdir, dirs1)
                print(dirs1)
                os.chdir(path)
                fl = glob.glob("%s/lfm*.h5" % (path))
                fl.sort()

                ch1 = 0
                DataDict = {}
                DataDict = {'freqlist': freqlist}
                DataDict['ch1'] = ch1
               
                if len(fl) > 1:
                    for jf, f in enumerate(fl):
                        print('jf=%d' %(jf))
                        #print('ch1=%d' %(ch1))
                        filter_ionograms(f, DataDict)
                    
                    if DataDict['ch1'] > 1:
                        save_var(DataDict)
                
