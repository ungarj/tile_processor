import os
from common import tiff_save


def config_subparser(rescale_parser):
    rescale_parser.add_argument("-x", required=True)
    rescale_parser.add_argument("-y", required=True)
    rescale_parser.add_argument("-i", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, metatile_xsize, metatile_ysize, *args, **kwargs):

    tile_xsize = parsed.tile_xsize[0]
    tile_ysize = parsed.tile_ysize[0]
    xresolution = float(parsed.x)
    yresolution = float(parsed.y)
    xscale = xresolution/tile_xsize
    yscale = yresolution/tile_ysize
    interpolation = parsed.i
    scalefactor = xresolution/tile_xsize
    rescaled_xsize = int(metatile_xsize*xscale)
    rescaled_ysize = int(metatile_ysize*yscale)
    process_rescale = "gdalwarp -ts %s %s -r %s -overwrite %s -of GTiff %s -srcnodata %s -dstnodata %s -multi > /dev/null" %(rescaled_xsize, rescaled_ysize, interpolation, temp_metatile, temp_processed, nodata, nodata)
    os.system(process_rescale)
    save_offsetx = int(save_offsetx*xscale)
    save_offsety = int(save_offsety*yscale)
    save_xsize = int(save_xsize*xscale)
    save_ysize = int(save_ysize*yscale)
    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)