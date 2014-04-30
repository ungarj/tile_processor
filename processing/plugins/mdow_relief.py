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
    azimuth1 = 260
    azimuth2 = 295
    azimuth3 = 335
    azimuth4 = 10

    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s -az %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, azimuth1, temp_metatile, temp_hillshade1)
    os.system(process_hillshade)
    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s -az %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, azimuth2, temp_metatile, temp_hillshade2)
    os.system(process_hillshade)
    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s -az %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, azimuth3, temp_metatile, temp_hillshade3)
    os.system(process_hillshade)
    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s -az %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, azimuth4, temp_metatile, temp_hillshade4)
    os.system(process_hillshade)
    nodata = 0
    ot = "-ot Byte"
    # open in numpy
    _, gt, _, nodata, temp_hillshade1_numpy = numpy_read(temp_hillshade1)
    _, gt, _, nodata, temp_hillshade2_numpy = numpy_read(temp_hillshade2)
    _, gt, _, nodata, temp_hillshade3_numpy = numpy_read(temp_hillshade3)
    _, gt, _, nodata, temp_hillshade4_numpy = numpy_read(temp_hillshade4)


    processed_numpy1 = numpy.minimum(temp_hillshade1_numpy, temp_hillshade2_numpy)
    processed_numpy2 = numpy.minimum(temp_hillshade3_numpy, temp_hillshade4_numpy)
    processed_numpy3 = numpy.minimum(processed_numpy1, processed_numpy2)

    processed_numpy = ndimage.median_filter(processed_numpy3, size=6)



    os.remove(temp_hillshade1)
    os.remove(temp_hillshade2)
    os.remove(temp_hillshade3)
    os.remove(temp_hillshade4)

    numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)