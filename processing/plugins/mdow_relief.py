import os
from scipy import ndimage
import numpy
from common import numpy_save, numpy_read


def config_subparser(mdow_relief_parser):
    mdow_relief_parser.add_argument("-s", required=True)
    mdow_relief_parser.add_argument("-z", required=True)
    mdow_relief_parser.add_argument("--alt", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    temp_hillshade1 = "/tmp/tmp_metatile_%s_1.tif" % os.getpid()
    temp_hillshade2 = "/tmp/tmp_metatile_%s_2.tif" % os.getpid()
    temp_hillshade3 = "/tmp/tmp_metatile_%s_3.tif" % os.getpid()
    temp_hillshade4 = "/tmp/tmp_metatile_%s_4.tif" % os.getpid()

    with open(temp_hillshade1, "w+"):
        pass
    with open(temp_hillshade2, "w+"):
        pass
    with open(temp_hillshade3, "w+"):
        pass
    with open(temp_hillshade4, "w+"):
        pass
    
    scale = parsed.s
    zfactor = parsed.z
    altitude = parsed.alt
    azimuth1 = 225
    azimuth2 = 270
    azimuth3 = 315
    azimuth4 = 360

    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, temp_metatile, temp_processed)
    os.system(process_hillshade)
    nodata = 0
    ot = "-ot Byte"
    # open in numpy
    _, gt, _, nodata, array_numpy = numpy_read(temp_processed)
    processed_numpy = ndimage.median_filter(array_numpy, size=3)
    numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)