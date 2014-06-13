import os
from common import numpy_read, numpy_save
from scipy import ndimage
import numpy
from osgeo import ogr, gdal, gdal_array
import psycopg2
#from pyspatialite import dbapi2 as db

def config_subparser(landcover_vectorize):
    landcover_vectorize.add_argument("-median", required=True)
    landcover_vectorize.add_argument("-table", required=True)


def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    _, gt, _, nodata, array_numpy = numpy_read(temp_metatile)


    #target_db = target.split(".")[0] + ".sqlite"
    targetdb = "geodata"
    dbuser = "ungarj"
    targettable = str(parsed.table)
    median = int(parsed.median)

    # geotransform values for tile
    xmin = gt[0] + (save_offsetx * gt[1])
    xmax = gt[0] + ((save_offsetx + save_xsize) * gt[1])
    ymin = gt[3] + ((save_offsety + save_ysize) * gt[5])
    ymax = gt[3] + (save_offsety * gt[5])

    # geotransform values for metatile
    save_offsetx = 0
    save_offsety = 0
    save_xsize = array_numpy.shape[1]
    save_ysize = array_numpy.shape[0]

    # reclassify
    '''
    11: cropland
    14: cropland
    20: cropland
    30: forest
    40: forest
    50: forest
    60: forest
    70: forest
    90: forest
    100: forest
    110: shrubland
    120: shrubland
    130: shrubland
    140: shrubland
    150: shrubland
    160: forest
    170: forest
    180: grassland
    190: sealed
    200: bare
    210: water
    220: ice
    230: nodata
    '''

    '''
    nodata: 0
    cropland: 1
    forest: 2
    shrubland: 3
    grassland: 4
    sealed: 5
    bare: 6
    water: 7
    ice: 8
    '''
    # vectorize (smooth edges)
    # smooth


    # reclassify
    ############
    classification = {
        11:1,
        14:1,
        20:1,
        30:2,
        40:2,
        50:2,
        60:2,
        70:2,
        90:2,
        100:2,
        110:3,
        120:3,
        130:3,
        140:3,
        150:3,
        160:2,
        170:2,
        180:4,
        190:5,
        200:6,
        210:7,
        220:8#,
        #230:0
    }

    temp_numpy = numpy.zeros((array_numpy.shape[0], array_numpy.shape[1]))
    
    for c in classification:
        idx = (array_numpy == c).nonzero()
        temp_numpy[idx] = classification[c]


    # median filter
    ###############
    processed_numpy = ndimage.median_filter(temp_numpy, size=median)


    #create Memory driver
    src_ds = gdal.Open( temp_metatile )
    format = "MEM"
    driver = gdal.GetDriverByName( format )
    mem_ds = driver.CreateCopy('', src_ds )
    # write filtered numpy array to GDAL band
    gdal_array.BandWriteArray(mem_ds.GetRasterBand(1), processed_numpy)
    mem_ds.GetRasterBand(1).WriteArray(processed_numpy)

    drv = ogr.GetDriverByName( 'Memory' )  
    ogr_ds = drv.CreateDataSource('out')  
    ogr_lyr = ogr_ds.CreateLayer('landcover')
    fieldname = 'type'
    field_defn = ogr.FieldDefn( fieldname, ogr.OFTInteger )
    ogr_lyr.CreateField(field_defn)
    ogr_field = ogr_lyr.GetLayerDefn().GetFieldIndex(fieldname)
    ogr_field = 0

    maskband = None
    
    gdal.Polygonize(mem_ds.GetRasterBand(1), maskband, ogr_lyr, ogr_field, [])

    
    # clip to tile boundary
    #######################
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xmin, ymin)
    ring.AddPoint(xmin, ymax)
    ring.AddPoint(xmax, ymax)
    ring.AddPoint(xmax, ymin)
    ring.AddPoint(xmin, ymin)
    clipbox = ogr.Geometry(ogr.wkbPolygon)
    clipbox.AddGeometry(ring)

    cliplayer = ogr_ds.CreateLayer('clipbox', geom_type=ogr.wkbPolygon)
    clipfeaturedefn = cliplayer.GetLayerDefn()
    clipfeature = ogr.Feature(clipfeaturedefn)
    clipfeature.SetGeometry(clipbox)
    cliplayer.CreateFeature(clipfeature)
    clipped = ogr_ds.CreateLayer('landcover_clipped', geom_type=ogr.wkbMultiPolygon)
    #clipped.ForceToMultiLineString()
    field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
    clipped.CreateField(field_defn)
    field_defn = ogr.FieldDefn('type', ogr.OFTInteger)
    clipped.CreateField(field_defn)

    ogr_lyr.Clip(cliplayer, clipped)

    connection = psycopg2.connect(database = targetdb, user = dbuser)
    # psql -d geodata -c "DROP TABLE landcover; CREATE TABLE landcover (id bigserial primary key, typeid double precision, type text);  SELECT AddGeometryColumn ('','landcover','the_geom',4326,'MULTIPOLYGON',2);"
    cursor = connection.cursor()


    for i in range(clipped.GetFeatureCount()):  
        insert = True
        feature = clipped.GetFeature(i)
        geometry = feature.GetGeometryRef()
        #print geometry.GetGeometryName()
        if geometry.GetGeometryName() in ("POLYGON", "MULTIPOLYGON") :
            continue
            #print "polygon"
        if geometry.GetGeometryName() == "GEOMETRYCOLLECTION" :
            geometry_new = ogr.Geometry(ogr.wkbMultiLineString)
            for i in xrange(geometry.GetGeometryCount()): 
                g = geometry.GetGeometryRef(i)
                if g.GetGeometryName() in ("POLYGON", "MULTIPOLYGON") :
                    #print "geometrycollection polygon"
                    geometry_new.AddGeometry(g.Clone())
                else:
                    print g.GetGeometryName()
            geometry = geometry_new
        if geometry.GetGeometryName() in ("LINESTRING", "MULTILINESTRING", "POINT", "MULTIPOINT") :
            insert = False

        if insert:
            lctype = feature.GetField("type")
            geometry.SetCoordinateDimension(2)
            wkt = geometry.ExportToWkt()
            cursor.execute("INSERT INTO " + targettable + " (type,the_geom) VALUES (%s, ST_Multi(ST_GeomFromText(%s, " +"4326)))", (lctype, wkt))
    connection.commit()  

    ogr_ds.Destroy()
    processed_numpy = []
    mem_ds = None



    #numpy_save(processed_numpy, target, save_offsetx, save_offsety, save_xsize, save_ysize, gt, nodata, ot)



    #processed_numpy = array_numpy
    #print "save processed_numpy"
    #print str(processed_numpy.shape[0]) + " " + str(processed_numpy.shape[1])

    
    cursor.close()
    connection.close()