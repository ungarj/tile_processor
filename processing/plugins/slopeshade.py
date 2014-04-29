import os
import numpy
from common import numpy_save, numpy_read


def config_subparser(slopeshade_parser):
    slopeshade_parser.add_argument("-s", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

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