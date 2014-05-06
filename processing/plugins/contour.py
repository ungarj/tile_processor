import os
from common import numpy_read, numpy_save
from scipy import ndimage
import numpy


def config_subparser(contour):
    contour.add_argument("-elevation", required=True)
    contour.add_argument("-median", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    target_db = target.split(".")[0] + ".sqlite"
    elevation = parsed.elevation
    median = parsed.median
    nodata = 0
 
    #print "read temp_metatile"
    _, gt, _, nodata, array_numpy = numpy_read(temp_metatile)
    processed_numpy = ndimage.median_filter(array_numpy, size=int(median))
    #processed_numpy = array_numpy
    #print "save processed_numpy"
    print str(processed_numpy.shape[0]) + " " + str(processed_numpy.shape[1])

    # geotransform values for tile
    xmin = gt[0] + (save_offsetx * gt[1])
    ymin = gt[3] + ((save_offsety + save_ysize) * gt[5])
    xmax = gt[0] + ((save_offsetx + save_xsize) * gt[1])
    ymax = gt[3] + (save_offsety * gt[5])

    # geotransform values for metatile
    save_offsetx = 0
    save_offsety = 0
    save_xsize = processed_numpy.shape[0]
    save_ysize = processed_numpy.shape[1]
    numpy_save(processed_numpy, temp_metatile, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)

    temp_target = "/tmp/temp_target_%s.sqlite" % os.getpid()

    process_contours = "gdal_contour -f 'SQLite' -i %s -a elev %s %s" %(elevation, temp_metatile, temp_target)
    #print process_contours
    os.system(process_contours)

    clip_contours ="ogr2ogr -f 'SQLite' -clipsrc %s %s %s %s %s %s" %(xmin, ymin, xmax, ymax, target_db, temp_target)
    os.system(clip_contours)

    os.remove(target)
    os.remove(temp_target)