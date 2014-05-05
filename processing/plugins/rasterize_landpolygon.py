import os
from common import tiff_save
import osgeo.gdal as gdal


def config_subparser(rasterize_landpolygon):
    rasterize_landpolygon.add_argument("-landpolygon", required=True)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    landpolygon = parsed.landpolygon

    temp_landpolygon = "/tmp/temp_landpolygon_%s.sqlite" % os.getpid()

    # get metattile extent
    ds = gdal.Open(temp_metatile)
    geotransform = ds.GetGeoTransform(1)
    xpixelsize = geotransform[1]
    ypixelsize = geotransform[5]
    width = ds.RasterXSize
    height = ds.RasterYSize

    llx = geotransform[0]
    lly = geotransform[3] + width*geotransform[4] + height*geotransform[5] 
    urx = geotransform[0] + width*geotransform[1] + height*geotransform[2] 
    ury = geotransform[3]

    # clip landpolygon
    print "clipping"
    clip_landpolygon = "ogr2ogr -clipsrc %s %s %s %s -f SQLite %s %s" %(llx, lly, urx, ury, temp_landpolygon, landpolygon)
    os.system(clip_landpolygon)

    # rasterize landpolygon
    print "rasterizing"
    rasterize_landpolygon = "gdal_rasterize -burn 1 -te %s %s %s %s -tr %s %s -ot Byte %s %s" %(llx, lly, urx, ury, xpixelsize, ypixelsize, temp_landpolygon, temp_processed)
    os.system(rasterize_landpolygon)
  
    if os.path.isfile(temp_landpolygon):
    	os.remove(temp_landpolygon)

    tiff_save(temp_processed, target, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot)   