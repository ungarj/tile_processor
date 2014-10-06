import os
from scipy import ndimage
import numpy
from common import numpy_save, numpy_read, tiff_save
import tempfile


def config_subparser(biggles_relief_parser):
    biggles_relief_parser.add_argument("-s", required=True)
    biggles_relief_parser.add_argument("-z", required=True)
    biggles_relief_parser.add_argument("--alt", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    scale = parsed.s
    zfactor = parsed.z
    altitude = parsed.alt

    temp_dem = tempfile.mktemp() #"/tmp/tmp_voids_raster_%s.tif" % os.getpid()
    with open(temp_dem, "w+"):
        pass

    nodata = 0

    _, gt, _, nodata, array_numpy = numpy_read(temp_metatile)


    processed_numpy = ndimage.gaussian_filter(array_numpy, 4)
    array_numpy = ndimage.median_filter(processed_numpy, size=5)
    processed_numpy = ndimage.gaussian_filter(array_numpy, 2)
    array_numpy = ndimage.median_filter(processed_numpy, size=5)
    processed_numpy = ndimage.median_filter(array_numpy, size=3)
    array_numpy = ndimage.gaussian_filter(processed_numpy, 1)
    

    # geotransform values for tile
    xmin = gt[0] + (save_offsetx * gt[1])
    xmax = gt[0] + ((save_offsetx + save_xsize) * gt[1])
    ymin = gt[3] + ((save_offsety + save_ysize) * gt[5])
    ymax = gt[3] + (save_offsety * gt[5])

    # geotransform values for metatile
    temp_save_offsetx = 0
    temp_save_offsety = 0
    temp_save_xsize = processed_numpy.shape[1]
    temp_save_ysize = processed_numpy.shape[0]

    numpy_save(array_numpy, temp_dem, temp_save_offsetx, temp_save_offsety, temp_save_xsize, temp_save_ysize, gt, nodata, ot)

    process_hillshade = "gdaldem hillshade -s %s -z %s -alt %s %s -of GTiff %s > /dev/null" %(scale, zfactor, altitude, temp_dem, temp_processed)
    os.system(process_hillshade)

    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)

    os.remove(temp_dem)