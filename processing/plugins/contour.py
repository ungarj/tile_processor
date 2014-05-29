import os
from common import numpy_read, numpy_save
from scipy import ndimage
import numpy
from osgeo import ogr, gdal, gdal_array
import psycopg2
#from pyspatialite import dbapi2 as db

def config_subparser(contour):
    contour.add_argument("-elevation", required=True)
    contour.add_argument("-median", required=True)
    contour.add_argument("-glacier_mask", required=False)

def process(parsed, target, temp_metatile, temp_processed, save_offsetx, save_offsety, save_xsize, save_ysize, nodata, ot, *args, **kwargs):

    #target_db = target.split(".")[0] + ".sqlite"
    target_db = "geodata"

    elevation = int(parsed.elevation)
    median = int(parsed.median)
    glacier_mask = parsed.glacier_mask
    nodata = 0
 
    #print "read temp_metatile"
    _, gt, _, nodata, array_numpy = numpy_read(temp_metatile)
    processed_numpy = ndimage.median_filter(array_numpy, size=median)
    #processed_numpy = array_numpy
    #print "save processed_numpy"
    #print str(processed_numpy.shape[0]) + " " + str(processed_numpy.shape[1])

    # geotransform values for tile
    xmin = gt[0] + (save_offsetx * gt[1])
    xmax = gt[0] + ((save_offsetx + save_xsize) * gt[1])
    ymin = gt[3] + ((save_offsety + save_ysize) * gt[5])
    ymax = gt[3] + (save_offsety * gt[5])

    # geotransform values for metatile
    save_offsetx = 0
    save_offsety = 0
    save_xsize = processed_numpy.shape[1]
    save_ysize = processed_numpy.shape[0]
    
    # create contours from processed_numpy
    ds = gdal.Open(temp_metatile)

    drv = ogr.GetDriverByName( 'Memory' )  
    ogr_ds = drv.CreateDataSource('out')  
    #ogr_ds = ogr.GetDriverByName('ESRI Shapefile').CreateDataSource('contours_ogr/contour.shp')
    ogr_lyr = ogr_ds.CreateLayer('contour', geom_type = ogr.wkbLineString25D)
    field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
    ogr_lyr.CreateField(field_defn)
    field_defn = ogr.FieldDefn('elev', ogr.OFTReal)
    ogr_lyr.CreateField(field_defn)

    #create Memory driver
    src_ds = gdal.Open( temp_metatile )
    format = "MEM"
    driver = gdal.GetDriverByName( format )
    mem_ds = driver.CreateCopy('', src_ds )
    # write filtered numpy array to GDAL band
    gdal_array.BandWriteArray(mem_ds.GetRasterBand(1), processed_numpy)
    mem_ds.GetRasterBand(1).WriteArray(processed_numpy)

    # write contours to OGR layer
    gdal.ContourGenerate(mem_ds.GetRasterBand(1), elevation, 0, [], 0, 0, ogr_lyr, 0, 1)

    # clip to tile boundary
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
    clipped = ogr_ds.CreateLayer('contour_clipped', geom_type = ogr.wkbLineString25D)
    field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
    clipped.CreateField(field_defn)
    field_defn = ogr.FieldDefn('elev', ogr.OFTReal)
    clipped.CreateField(field_defn)

    ogr_lyr.Clip(cliplayer, clipped)

    # PostGIS connection
    #connection = db.connect('contours.sqlite')
    connection = psycopg2.connect(database = 'geodata', user = 'ungarj')
    # psql -d geodata -c "DROP TABLE contours; CREATE TABLE contours (id bigserial primary key, elev double precision, type text);  SELECT AddGeometryColumn ('','contours','the_geom',4326,'MULTILINESTRING',25D);"
    cursor = connection.cursor()

    if glacier_mask:
        # read glacier_mask
        shapefile = glacier_mask
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(shapefile, 0)
        glacier_layer = dataSource.GetLayer()

        #print "processing glacier contours"    
        # clip & save glacier contours
        glacier_clipped = ogr_ds.CreateLayer('contour_clipped', geom_type = ogr.wkbLineString25D)
        field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
        glacier_clipped.CreateField(field_defn)
        field_defn = ogr.FieldDefn('elev', ogr.OFTReal)
        glacier_clipped.CreateField(field_defn)
    
        clipped.Clip(glacier_layer, glacier_clipped)

        contour_type = "glaciated"

        for i in range(glacier_clipped.GetFeatureCount()):  
            feature = glacier_clipped.GetFeature(i)  
            elev = feature.GetField("elev")
            wkt = feature.GetGeometryRef().ExportToWkt() 
            cursor.execute("INSERT INTO contours (elev,the_geom,type) VALUES (%s, ST_Multi(ST_GeomFromText(%s, " +"4326)), %s)", (str(elev), wkt, contour_type))
        connection.commit()

        #print "processing land contours"
        # clip & save land contours
        land_clipped = ogr_ds.CreateLayer('contour_clipped', geom_type = ogr.wkbLineString25D)
        field_defn = ogr.FieldDefn('ID', ogr.OFTInteger)
        land_clipped.CreateField(field_defn)
        field_defn = ogr.FieldDefn('elev', ogr.OFTReal)
        land_clipped.CreateField(field_defn)
    
        clipped.Erase(glacier_layer, land_clipped)

        contour_type = "land"

        for i in range(land_clipped.GetFeatureCount()):  
            feature = land_clipped.GetFeature(i)  
            elev = feature.GetField("elev")
            wkt = feature.GetGeometryRef().ExportToWkt() 
            cursor.execute("INSERT INTO contours (elev,the_geom,type) VALUES (%s, ST_Multi(ST_GeomFromText(%s, " +"4326)), %s)", (str(elev), wkt, contour_type))
        connection.commit()  

    
    else:
        # save to POSTGIS
        for i in range(clipped.GetFeatureCount()):  
            feature = clipped.GetFeature(i)  
            elev = feature.GetField("elev")
            wkt = feature.GetGeometryRef().ExportToWkt() 
            cursor.execute("INSERT INTO contours (elev,the_geom) VALUES (%s, ST_Multi(ST_GeomFromText(%s, " +"4326)))", (str(elev), wkt))
        connection.commit()  

  
    #os.remove(target)
    #os.remove(temp_target)

    cursor.close()
    connection.close()