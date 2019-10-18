#!/usr/bin/env python3

'''
Simple commandline tool to calculate weighted wind fetch using a raster stack
of wind fetch lengths determined with the WindFetchSimple tool.

This tool read the fetch output and outputs a weigted mean fetch raster using
the supplied weights. Number of weights should be equal to number of fetch
directions and sum to 1. 
'''

def main():
    import numpy as np
    import rasterio
    import argparse
    import os 

    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help = "Path to input fetch raster file", 
                        required = True, type = os.path.abspath)
    parser.add_argument("-o", "--output", help = "Path to output weighted fetch raster file", 
                        required = True, type = os.path.abspath)
    parser.add_argument("-w", "--weights", help = "Weight of each direction in input file as comma-seperated string e.g. -d '0.3,0.3,0.4'.", required = True)
     
    args = parser.parse_args()
    
    filein = args.input
    fileout = args.output
    weights = args.weights

    print("Reading raster file from " + filein)
    with rasterio.open(filein) as ds_in:
        arr_in = ds_in.read().astype("float")
        meta_in = ds_in.profile
        bands, nrow, ncol = arr_in.shape
    

    weights = np.array([float(i) for i in weights.split(",")])
    
    if len(weights) != bands:
        print('Error: Number of weights not equal to number of bands in input raster')
        return(1)
        
    if sum(weights) > 1.01 or sum(weights) < 0.99:
        print('Error: Sum of weights not equal to 1. The sum of the supplied weights is {}'.format(sum(weights)))
        return(1)
    
    arr_in_w = np.tensordot(arr_in, weights, axes = ([0],[0]))
    
    meta_in["count"] = 1
    meta_in["dtype"] = "float64"
    meta_in["nodata"] = 0
    
    print("Writing weighted fetch raster file to " + fileout)
    with rasterio.open(fileout, "w", **meta_in) as dst:
        dst.write(np.expand_dims(arr_in_w, axis=0))
    
if __name__ == "__main__":
    main()
