import os
from common import tiff_save


def config_subparser(fillnodata_parser):
    pass

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    process_fillnodata = "gdal_fillnodata.py %s %s > /dev/null" %(temp_metatile, temp_processed)
    os.system(process_fillnodata)
    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)