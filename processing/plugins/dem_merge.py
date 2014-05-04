import os
import numpy
from common import numpy_save, numpy_read
import tempfile


def config_subparser(dem_merge_parser):
    dem_merge_parser.add_argument("-voids", required=True)
    dem_merge_parser.add_argument("-secondary", required=True)
    dem_merge_parser.add_argument("-tertiary", required=False)
    dem_merge_parser.add_argument("-landpolygon", required=False)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    temp_voids = tempfile.mktemp() + ".geojson" #"tmp_voids_%s.geojson" % os.getpid()
    with open(temp_voids, "w+"):
        pass
    temp_voids_raster = tempfile.mktemp() #"/tmp/tmp_voids_raster_%s.tif" % os.getpid()
    with open(temp_voids_raster, "w+"):
        pass


    temp_secondary = "/tmp/tmp_secondary_%s" % os.getpid()
    with open(temp_voids, "w+"):
        pass

    void_mask = parsed.voids
    secondary_source = parsed.secondary
    tertiary_source = parsed.tertiary

    nodata = 0
    ot = "-ot Int16"

    # read primary data
    _, gt, _, nodata, primary_dem = numpy_read(temp_metatile)

    # TODO check if valid
    ulx, llx = gt[0], gt[0]
    uly, ury = gt[3], gt[3]
    urx, lrx = ulx + (gt[1] * primary_dem.shape[1]), ulx + (gt[1] * primary_dem.shape[1])
    lly, lry = uly + (gt[5] * primary_dem.shape[0]), uly + (gt[5] * primary_dem.shape[0])

    # read secondary
    clip_secondary = "gdal_translate -projwin %s %s %s %s %s %s" %(ulx, uly, lrx, lry, secondary_source, temp_secondary)
    print clip_secondary
    os.system(clip_secondary)
    _, gt, _, nodata, secondary_dem = numpy_read(temp_secondary)

    # clip void mask
    os.remove(temp_voids)
    clip_void_mask = "ogr2ogr -overwrite -f 'GeoJSON' %s %s -clipsrc %s %s %s %s" %(temp_voids, void_mask, llx, lly, urx, ury)
    print clip_void_mask
    os.system(clip_void_mask)
    
    # rasterize void mask
    rasterize_void_mask = "gdal_rasterize -burn 1 -i -te %s %s %s %s -tr %s %s -ot Byte %s %s" %(llx, lly, urx, ury, gt[1], -gt[5], temp_voids, temp_voids_raster)
    print rasterize_void_mask
    os.system(rasterize_void_mask)
    _, gt, _, nodata, void_mask_raster = numpy_read(temp_voids_raster)
    
    ## numpy_read
    
    # fill gaps by overlaying numpy arrays
    # http://stackoverflow.com/questions/19817955/overlay-part-of-the-matrix-on-top-of-another

    # clip
    ## gdalwarp -cutline -cl 

    #print array_numpy.shape
    #processed_temp = numpy.multiply(primary_dem, void_mask_raster)   #print processed_numpy[1][3]
    processed_numpy = numpy.where(void_mask_raster != 0, primary_dem, secondary_dem)

    # clean up
    os.remove(temp_voids)
    os.remove(temp_voids_raster)
    #os.remove(temp_secondary)

    numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)