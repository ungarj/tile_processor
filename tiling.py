#!/usr/bin/env python
#
## Copyright (c) 2013
##
## Joachim Ungar (ju@eox.at)
##
## Permission is hereby granted, free of charge, to any person obtaining a copy 
## of this software and associated documentation files (the "Software"), to deal 
## in the Software without restriction, including without limitation the rights 
## to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
## copies of the Software, and to permit persons to whom the Software is furnished
##  to do so, subject to the following conditions:
##
## The above copyright notice and this permission notice shall be included in all 
## copies or substantial portions of the Software.
##
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
## SOFTWARE.

import sys
import argparse
import os
import osgeo.gdal as gdal
import osgeo.gdalconst as gdalconst
from osgeo.gdalconst import *
import subprocess
import numpy
#from numpy import *
import osr

# Configuration
# =============

SOURCE_X=0
SOURCE_Y=0
# number of digits in tile naming (e.g. X001Y001)
DIGITS=3


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("source_vrt", nargs=1, type=str)
    parser.add_argument("tile_xsize", nargs=1, type=int)
    parser.add_argument("tile_ysize", nargs=1, type=int)
    parser.add_argument("margin", nargs=1, type=int)
    parser.add_argument("dest", nargs=1, type=str)
    parser.add_argument("--create_vrt", action="store_true")

    subparsers = parser.add_subparsers(help='sub-command help')
    fillnodata_parser = subparsers.add_parser("fillnodata")
    hillshade_parser = subparsers.add_parser("hillshade")
    slopeshade_parser = subparsers.add_parser("slopeshade")
    rescale_parser = subparsers.add_parser("rescale")
    tiling_parser = subparsers.add_parser("tiling")

    hillshade_parser.add_argument("-s", required=True)
    hillshade_parser.add_argument("-z", required=True)
    hillshade_parser.add_argument("--alt", required=True)

    slopeshade_parser.add_argument("-s")

    rescale_parser.add_argument("-x", required=True)
    rescale_parser.add_argument("-y", required=True)
    rescale_parser.add_argument("-i", required=True)

    fillnodata_parser.set_defaults(method="fillnodata")
    hillshade_parser.set_defaults(method="hillshade")
    slopeshade_parser.set_defaults(method="slopeshade")
    rescale_parser.set_defaults(method="rescale")
    tiling_parser.set_defaults(method="tiling")

    parsed = parser.parse_args(args)

    print parsed.method

    source_vrt = parsed.source_vrt[0]
    source = str(source_vrt)
    tile_xsize = parsed.tile_xsize[0]
    tile_ysize = parsed.tile_ysize[0]
    margin = parsed.margin[0]
    dest = parsed.dest[0]

    print parsed.create_vrt
    
    ds = gdal.Open(source, GA_ReadOnly)

    # determine VRT pixel size
    vrt_xsize = ds.RasterXSize
    vrt_ysize = ds.RasterYSize
    print vrt_xsize, vrt_ysize

    #TODO determine tile numbers
    tile_count_x = int(vrt_xsize / tile_xsize)
    tile_count_y = int(vrt_ysize / tile_ysize)
    print tile_count_x, tile_count_y

    temp_metatile = "temp_metatile.tif"
    temp_processed = "temp_processed.tif"

    for i in range(0,tile_count_x):
        for j in range(0,tile_count_y):

#    for i in range(0,10):
#        for j in range(0,10):

            # pass if tile will contain exclusively nodata values

            # determine tile boundaries
            tile_offsetx = SOURCE_X + i*tile_xsize
            tile_offsety = SOURCE_Y + j*tile_ysize
            #print "srcwin %s %s %s %s" %(tile_offsetx, tile_offsety, tile_xsize, tile_ysize)      
            
            #TODO calculate metatile boundaries
            metatile_offsetx = tile_offsetx - margin
            metatile_xsize = tile_xsize + 2 * margin
            if (metatile_offsetx < 0):
                metatile_offsetx = 0
                metatile_xsize = tile_ysize + margin

            metatile_offsety = tile_offsety - margin
            metatile_ysize = tile_ysize + 2 * margin
            if (metatile_offsety < 0):
                metatile_offsety = 0
                metatile_ysize = tile_ysize + margin

            cropx=False
            cropy=False

            if (metatile_offsetx+metatile_xsize > vrt_xsize):
                metatile_xsize = metatile_xsize - margin
                
            if (metatile_offsety+metatile_ysize > vrt_ysize):
                metatile_ysize = metatile_ysize - margin

            if (metatile_offsetx == 0):
                metatile_xsize = metatile_xsize - margin
                cropx = True
                
            if (metatile_offsety == 0):
                metatile_ysize = metatile_ysize - margin
                cropy = True

            band = ds.GetRasterBand(1)
            nodata = int(band.GetNoDataValue())
            data = numpy.array(band.ReadAsArray(tile_offsetx, tile_offsety, tile_xsize, tile_ysize))
            #print "%s %s %s %s" %(tile_offsetx, tile_offsety, tile_xsize, tile_ysize)
            
            # skip if tile is empty
            if numpy.all(data==nodata):
                print "nothing to be written\n"
            else:
                print "data found"
                #print "srcwin %s %s %s %s" %(metatile_offsetx, metatile_offsety, metatile_xsize, metatile_ysize)

                save_metatile = "gdal_translate %s -of GTiff %s -srcwin %s %s %s %s" %(source_vrt, temp_metatile, metatile_offsetx, metatile_offsety, metatile_xsize, metatile_ysize)
                print save_metatile
                os.system(save_metatile)

                #TODO crop to tile boundaries & save
                save_offsetx = margin
                save_offsety = margin
                save_xsize = tile_xsize
                save_ysize = tile_ysize
                #print "cropx = " + str(cropx)
                #print "cropx = " + str(cropy)
                if (cropx==True):
                    save_offsetx = 0
                if (cropy==True):
                    save_offsety = 0

                if not os.path.exists(dest):
                    os.makedirs(dest)      
                target = dest+"X"+str(i).zfill(DIGITS)+"Y"+str(j).zfill(DIGITS)+".tif"

                ot = ""


                #TODO apply processing

                if (parsed.method == "hillshade"):
                    scale = parsed.s
                    zfactor = parsed.z
                    altitude = parsed.alt

                    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s %s -of GTiff %s" %(scale, zfactor, altitude, temp_metatile, temp_processed)
                    print process_hillshade
                    os.system(process_hillshade)

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "slopeshade"):
                    scale = parsed.s

                    process_slopeshade = "gdaldem slope -s %s %s -of GTiff %s" %(scale, temp_metatile, temp_processed)
                    print process_slopeshade
                    os.system(process_slopeshade)

                    nodata = 0
                    ot = "-ot Byte"

                    data_numpy = numpy_read(temp_processed)

                    array_numpy = data_numpy[4]
                    nodata = data_numpy[3]
                    print array_numpy

                    print nodata

                    # replace nodata values with 0
                    #for i in numpy.iteritems():
                    array_numpy[array_numpy==nodata] = 0

                    # convert to 8 bit and invert values
                    array_numpy = -(array_numpy.astype(numpy.uint8)-255)
                    array_numpy[array_numpy==0] = 255

                    print array_numpy

                    processed_numpy = data_numpy
                    #print processed_numpy[1][3]

                    numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "fillnodata"):
                    process_fillnodata = "gdal_fillnodata.py %s %s" %(temp_metatile, temp_processed)
                    print process_fillnodata
                    os.system(process_fillnodata)

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "rescale"):
                    xscale = int(parsed.x)*tile_xsize
                    yscale = int(parsed.y)*tile_ysize
                    interpolation = parsed.i

                    process_rescale = "gdalwarp -ts %s %s -r %s -overwrite %s -of GTiff %s" %(xscale, yscale, interpolation, temp_metatile, temp_processed)
                    print process_rescale
                    os.system(process_rescale)

                    save_offsetx = save_offsetx*3
                    save_offsety = save_offsety*3
                    save_xsize = save_xsize*3
                    save_ysize = save_ysize*3

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "tiling"):
                    temp_processed = temp_metatile

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                print "tile processed\n"

    # create VRT
    if parsed.create_vrt:
        target_vrt = dest.rsplit("/")[0] + ".vrt"
        target_tiffs = dest + "*"
        create_vrt = "gdalbuildvrt -overwrite %s %s -vrtnodata %s" %(target_vrt, target_tiffs, nodata)
        print create_vrt
        os.system(create_vrt)

    # clean up
    clean = "rm -f %s %s" %(temp_metatile, temp_processed)
    os.system(clean)

def tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot):
    save_tile = "gdal_translate -co compress=lzw %s -of GTiff %s -srcwin %s %s %s %s -a_nodata %s %s" %(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)
    print save_tile
    os.system(save_tile)

def numpy_read(gtiff):
    # TEST: print geo metadata
    temp_ds = gdal.Open(gtiff, GA_ReadOnly)
    temp_geotransform = temp_ds.GetGeoTransform()

    temp_band = temp_ds.GetRasterBand(1)
    temp_nodata = int(temp_band.GetNoDataValue())
    temp_data = numpy.array(temp_band.ReadAsArray())

    return temp_ds, temp_geotransform, temp_band, temp_nodata, temp_data

def numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot):
    #TODO save numpy array as GTiff
    #xmin,ymin,xmax,ymax = 
    xmin = processed_numpy[1][0]
    ymax = processed_numpy[1][3]
    nrows,ncols = numpy.shape(processed_numpy[4])
    xres = processed_numpy[1][1]
    yres = -processed_numpy[1][5]
    geotransform=(xmin,xres,0,ymax,0, -yres)   
    # That's (top left x, w-e pixel resolution, rotation (0 if North is up), 
    #         top left y, rotation (0 if North is up), n-s pixel resolution)
    # I don't know why rotation is in twice???

    output_raster = gdal.GetDriverByName('GTiff').Create(target,ncols, nrows, 1 ,gdal.GDT_Byte)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()                 # Establish its coordinate encoding
    srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
                                                 # Anyone know how to specify the 
                                                 # IAU2000:49900 Mars encoding?
    output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system 
                                                       # to the file
    #print "xmin %s ymax %s nrows %s ncols %s xres %s yres %s" %(xmin, ymax, nrows, ncols, xres, yres)
    output_raster.GetRasterBand(1).WriteArray(processed_numpy[4])   # Writes my array to the raster

if __name__ == "__main__":
        main(sys.argv[1:])

