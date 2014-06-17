import os
from scipy import ndimage
import numpy
from common import numpy_save, numpy_read


def config_subparser(biggles_relief_parser):
    biggles_relief_parser.add_argument("-s", required=True)
    biggles_relief_parser.add_argument("-z", required=True)
    biggles_relief_parser.add_argument("--alt", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    scale = parsed.s
    zfactor = parsed.z
    altitude = parsed.alt
    
    _, gt, _, nodata, array_metatile = numpy_read(temp_metatile)
    #os.remove(temp_metatile)

    filtered_numpy = ndimage.median_filter(array_metatile, size=3)
    array_metatile = []
    array_metatile = ndimage.median_filter(filtered_numpy, size=5)
    filtered_numpy = []
    filtered_numpy = ndimage.median_filter(array_metatile, size=3)

    numpy_save(filtered_numpy, temp_metatile, 0, 0, filtered_numpy.shape[0], filtered_numpy.shape[1], gt, nodata, ot)

    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, temp_metatile, temp_processed)
    os.system(process_hillshade)
    nodata = 0
    ot = "-ot Byte"
    # open in numpy
    _, gt, _, nodata, array_numpy = numpy_read(temp_processed)
    processed_numpy = ndimage.median_filter(array_numpy, size=3)
    array_numpy = []
    array_numpy = ndimage.median_filter(processed_numpy, size=3)
    processed_numpy = []
    processed_numpy = ndimage.median_filter(array_numpy, size=3)
    array_numpy = []
    array_numpy = ndimage.median_filter(processed_numpy, size=3)
    processed_numpy = []
    processed_numpy = ndimage.median_filter(array_numpy, size=3)

    numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)

    #os.remove(temp_metatile)