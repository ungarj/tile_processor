tile_processor
==============

tile-based batch processing for DEM data

This script is designed to process huge chunks of DEM data (e.g. global SRTM coverage). It makes use of GDAL's [VRT format](http://www.gdal.org/gdal_vrttut.html), cuts out tiles and applies the desired processing. Currently
 * basic tiling (gdal_translate),
 * hillshade (gdaldem),
 * slopeshade (gdaldem),
 * rescale (gdalwarp), and
 * fillnodata (gdal_fillnodata.py)

are supported. 
