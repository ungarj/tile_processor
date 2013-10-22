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
import tempfile
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
    parser.add_argument("--naming_srtm", action="store_true")
    parser.add_argument("--resume", action="store_true")

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

    #print parsed.method

    source_vrt = parsed.source_vrt[0]
    source = str(source_vrt)
    tile_xsize = parsed.tile_xsize[0]
    tile_ysize = parsed.tile_ysize[0]
    margin = parsed.margin[0]
    dest = parsed.dest[0]

    #print parsed.create_vrt
    
    ds = gdal.Open(source, GA_ReadOnly)

    # determine VRT pixel size
    vrt_xsize = ds.RasterXSize
    vrt_ysize = ds.RasterYSize
    print vrt_xsize, vrt_ysize

    # determine tile numbers
    tile_count_x = int(numpy.ceil(float(vrt_xsize)/float(tile_xsize)))
    tile_count_y = int(numpy.ceil(float(vrt_ysize)/float(tile_ysize)))
    print tile_count_x, tile_count_y
    
    temp_metatile = tempfile.mktemp()#= "temp_metatile.tif"
    temp_processed = tempfile.mktemp() #"temp_processed.tif"
    
    if (parsed.method == "rescale"):
        # determine scalefactor
        tile_xsize = parsed.tile_xsize[0]
        tile_ysize = parsed.tile_ysize[0]

        xresolution = float(parsed.x)
        yresolution = float(parsed.y)

        xscale = xresolution/tile_xsize
        yscale = yresolution/tile_ysize
    
        vrt_xsize = int(int(vrt_xsize*xscale)/xscale)
        vrt_ysize = int(int(vrt_ysize*yscale)/yscale)
        
        #print vrt_xsize, vrt_ysize
    
    for i in range(0,tile_count_x):
        for j in range(0,tile_count_y):
            
            tile_xsize = parsed.tile_xsize[0]
            tile_ysize = parsed.tile_ysize[0]

            # determine tile boundaries
            tile_offsetx = SOURCE_X + i*tile_xsize
            tile_offsety = SOURCE_Y + j*tile_ysize

            # reduce tile size if end of column/row                
            if i==tile_count_x-1 and (vrt_xsize-(i*tile_xsize)!=0):
                tile_xsize = vrt_xsize-i*tile_xsize            
            if j==tile_count_y-1 and (vrt_ysize-(j*tile_ysize)!=0):
                tile_ysize = vrt_ysize-j*tile_ysize

            #calculate metatile boundaries
            metatile_offsetx = tile_offsetx - margin
            metatile_xsize = tile_xsize + 2 * margin

            metatile_offsety = tile_offsety - margin
            metatile_ysize = tile_ysize + 2 * margin

            #TODO crop to tile boundaries & save
            save_offsetx = margin
            save_offsety = margin
            save_xsize = tile_xsize
            save_ysize = tile_ysize
                
            # clip metatile if outside of input file's boundaries
            # if negative, set save_offset to 0 and make metatile-margin
            # if out of max, make metatile-margin
            if (metatile_offsetx<0):
                metatile_offsetx=0
                save_offsetx=0
                metatile_xsize=metatile_xsize-margin
                #print "CROP X"

            if (metatile_offsety<0):
                metatile_offsety=0
                save_offsety=0
                metatile_ysize=metatile_ysize-margin
                #print "CROP Y"

            if (metatile_offsetx+metatile_xsize > vrt_xsize):
                metatile_xsize = metatile_xsize - margin

            if (metatile_offsety+metatile_ysize > vrt_ysize):
                metatile_ysize = metatile_ysize - margin

            print metatile_xsize
            print metatile_ysize

            band = ds.GetRasterBand(1)
            nodata = int(band.GetNoDataValue() or 0)
            data = numpy.array(band.ReadAsArray(tile_offsetx, tile_offsety, tile_xsize, tile_ysize))


            # define output tile name
            target = dest+"X"+str(i).zfill(DIGITS)+"Y"+str(j).zfill(DIGITS)+".tif"

            ot = ""

            if parsed.naming_srtm:
                #print "save as SRTM named tile"
                geotransform = ds.GetGeoTransform(1)
                xpixelsize = geotransform[1]
                ypixelsize = geotransform[5]
                xorigin = geotransform[0]
                yorigin = geotransform[3]
                lon_character = "E"
                lat_character = "N"

                lon_number = int(round(xorigin + xpixelsize*tile_offsetx))
                if lon_number<0:
                    lon_number=-lon_number
                    lon_character = "W"

                lat_number = int(round(yorigin + ypixelsize*(tile_offsety+tile_ysize)))
                if lat_number<0:
                    lat_number=-lat_number
                    lat_character = "S"

                target = dest+lat_character+str(lat_number).zfill(2)+lon_character+str(lon_number).zfill(3)+".tif"

            tile_exists = False
            if parsed.resume:
                #check whether target tile exists
                tile_exists = os.path.isfile(target)
            
            print "\n"
            print "processing tile " + target

            # skip if tile is empty
            data[data==0]=nodata
            if numpy.all(data==nodata):
                print "source data empty, skipping"
            elif (tile_exists==True):
                print "tile exists, skipping"    
            else:                
                #print "data found"
                #print "srcwin %s %s %s %s" %(metatile_offsetx, metatile_offsety, metatile_xsize, metatile_ysize)

                save_metatile = "gdal_translate %s -of GTiff %s -srcwin %s %s %s %s > /dev/null" %(source_vrt, temp_metatile, metatile_offsetx, metatile_offsety, metatile_xsize, metatile_ysize)
                #print save_metatile
                os.system(save_metatile)

                if not os.path.exists(dest):
                    os.makedirs(dest)      
                
                #TODO apply processing

                if (parsed.method == "hillshade"):
                    scale = parsed.s
                    zfactor = parsed.z
                    altitude = parsed.alt

                    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, temp_metatile, temp_processed)
                    #print process_hillshade
                    os.system(process_hillshade)

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "slopeshade"):
                    scale = parsed.s

                    process_slopeshade = "gdaldem slope -s %s %s -of GTiff %s > /dev/null" %(scale, temp_metatile, temp_processed)
                    os.system(process_slopeshade)

                    nodata = 0
                    ot = "-ot Byte"

                    _, gt, _, nodata, array_numpy = numpy_read(temp_processed)

                    array_numpy[array_numpy==nodata] = 0

                    # convert to 8 bit and invert values
                    array_numpy = -(array_numpy.astype(numpy.uint8)-255)
                    array_numpy[array_numpy==0] = 255

                    #print array_numpy.shape

                    processed_numpy = array_numpy
                    #print processed_numpy[1][3]

                    numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)

                if (parsed.method == "fillnodata"):
                    process_fillnodata = "gdal_fillnodata.py %s %s > /dev/null" %(temp_metatile, temp_processed)
                    os.system(process_fillnodata)

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "rescale"):
                    interpolation = parsed.i

                    scalefactor = xresolution/tile_xsize
                    rescaled_xsize = int(metatile_xsize*xscale)
                    rescaled_ysize = int(metatile_ysize*yscale)
                    print rescaled_xsize, rescaled_ysize

                    process_rescale = "gdalwarp -ts %s %s -r %s -overwrite %s -of GTiff %s -srcnodata %s -dstnodata %s -multi > /dev/null" %(rescaled_xsize, rescaled_ysize, interpolation, temp_metatile, temp_processed, nodata, nodata)
                    print process_rescale
                    os.system(process_rescale)

                    save_offsetx = int(save_offsetx*xscale)
                    save_offsety = int(save_offsety*yscale)
                    save_xsize = rescaled_xsize
                    save_ysize = rescaled_ysize

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

                if (parsed.method == "tiling"):
                    temp_processed = temp_metatile

                    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)                    

                print "tile processed\n"

    # create VRT
    if parsed.create_vrt:
        target_vrt = dest.rsplit("/")[0] + ".vrt"
        target_tiffs = dest + "*.tif"
        create_vrt = "gdalbuildvrt -overwrite %s %s" %(target_vrt, target_tiffs)
        print create_vrt
        os.system(create_vrt)

    # clean up
    os.remove(temp_metatile)
    os.remove(temp_processed)

def tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot):
    save_tile = "gdal_translate -co compress=lzw %s -of GTiff %s -srcwin %s %s %s %s -a_nodata %s %s > /dev/null" %(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)
    print save_tile
    os.system(save_tile)

def numpy_read(gtiff):
    temp_ds = gdal.Open(gtiff, GA_ReadOnly)
    temp_geotransform = temp_ds.GetGeoTransform()

    temp_band = temp_ds.GetRasterBand(1)
    temp_nodata = int(temp_band.GetNoDataValue() or 0)
    temp_data = numpy.array(temp_band.ReadAsArray())

    return temp_ds, temp_geotransform, temp_band, temp_nodata, temp_data

def numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, geotransform_original, nodata, ot):

    cut_array = processed_numpy[save_offsety:save_offsety + save_ysize, save_offsetx:save_offsetx + save_xsize]

    geotransform = [
        geotransform_original[0] + geotransform_original[1] * save_offsetx,
        geotransform_original[1],
        geotransform_original[2],
        geotransform_original[3] + geotransform_original[5] * save_offsety,
        geotransform_original[4],
        geotransform_original[5]
    ]

    output_raster = gdal.GetDriverByName('GTiff').Create(target, save_xsize, save_ysize, 1, gdal.GDT_Byte)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()                 # Establish its coordinate encoding
    srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
                                                 # Anyone know how to specify the 
                                                 # IAU2000:49900 Mars encoding?
    output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system 
                                                       # to the file
    output_raster.GetRasterBand(1).WriteArray(cut_array)   # Writes my array to the raster

if __name__ == "__main__":
        main(sys.argv[1:])
