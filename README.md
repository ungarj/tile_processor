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

usage
-----

`./tiling.py path/to/source/vrt 1200 1200 0 --naming_srtm --create_vrt output-dir/ tiling`

Creates 1200 x 1200 pixel tiles, applies the SRTM naming scheme (e.g. N40W120.tif) for output tiles. Tiles will be written into output-dir and a VRT with the same name will be created.


`./tiling.py path/to/source/vrt 1200 1200 10 --naming_srtm --create_vrt output-dir/ fillnodata`

Fills gaps using the gdal_fillnodata.py script. This time, a 10 pixel buffer is used around each tile.


`./tiling.py path/to/source/vrt 1200 1200 0 --naming_srtm --create_vrt output-dir/ rescale -x 3 -y 3 -i lanczos`

Cuts out tiles and rescales each tile by factor 3 (-x 3 -y 3) using lanczos interpolation.


`./tiling.py path/to/source/vrt 3600 3600 6 --naming_srtm --create_vrt output-dir/ hillshade -s 111120 -z 1 --alt 80`

Processes hillshade using a 6 px buffer.


`./tiling.py path/to/source/vrt 3600 3600 6 --naming_srtm --create_vrt output-dir/ slopeshade -s 111120`

Processes slopeshade using a 6 px buffer.
