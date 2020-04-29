#!/usr/bin/env python3


"""Reads the EXIF headers from geo-tagged photos. and creates a KML file.

Reads the EXIF headers from geo-tagged photos and creates a KML file mapping each photo as a 
labelled point on the map

Includes refactored code from the googlearchives:
https://github.com/googlearchive/js-v2-samples/blob/gh-pages/articles-geotagsimple/exif2kml.py
with thanks to author mmarks@google.com (Mano Marks)
 
  GetFile(): Handles the opening of an individual file.
  GetHeaders(): Reads the headers from the file.
  DmsToDecimal(): Converts EXIF GPS headers data to a decimal degree.
  GetGps(): Parses out the the GPS headers from the headers data.
  CreateKmlDoc(): Creates an XML document object to represent the KML document.
  CreatePhotoOverlay: Creates an individual PhotoOverlay XML element object.
  CreateKmlFile(): Creates and writes out a KML document to file.
"""

__author__ = "nicholas.ss.harris@gmail.com (Nicholas Harris)"

import sys
import xml.dom.minidom
import exifread


def dms_to_decimal(deg_num, deg_den, 
                    min_num, min_den,
                    sec_num, sec_den):

    
    degree = deg_num / deg_den
    minute = min_num / min_den / 60
    second = sec_num / sec_den / 3600

    return degree + minute + second


def grab_gps(file_data):
    """Grabs GPS metadata from EXIF header of a file

        Key: GPS GPSVersionID, value [2, 2, 0, 0]
        Key: GPS GPSLatitudeRef, value N
        Key: GPS GPSLatitude, value [48, 16, 579/100]
        Key: GPS GPSLongitudeRef, value E
        Key: GPS GPSLongitude, value [11, 36, 121/10]
        Key: GPS GPSAltitudeRef, value 0
        Key: GPS GPSAltitude, value 10801/20
        Key: GPS GPSTimeStamp, value [17, 31, 16]
        Key: GPS GPSDOP, value 10
        Key: GPS GPSProcessingMethod, value [65, 83, 67, 73, 73, 0, 0, 0, 102, 117, 115, 101, 100]
        Key: GPS GPSDate, value 2018:08:29
        Key: Image GPSInfo, value 21009
        Key: Image DateTime, value 2018:08:29 19:31:19 # When the file was changed?

    Args:
        file_data:
        
    Return:
        GPS tags as a dictionary of strings of ALTITUDE, DATETIME, LAT, LONG
    """
    header = exifread.process_file(file_data, details=False)

    lat_dms = header["GPS GPSLatitude"].values
    long_dms = header["GPS GPSLongitude"].values

    latitude = dms_to_decimal(  lat_dms[0].num, lat_dms[0].den,
                                lat_dms[1].num, lat_dms[1].den,
                                lat_dms[2].num, lat_dms[2].den)
    longitude = dms_to_decimal( long_dms[0].num, long_dms[0].den,
                                long_dms[1].num, long_dms[1].den,
                                long_dms[2].num, long_dms[2].den)

    if header['GPS GPSLatitudeRef'].printable  == 'S': 
        latitude  *= -1
    if header['GPS GPSLongitudeRef'].printable == 'W': 
        longitude *= -1

    altitude = None

    if 'GPS GPSAltitude' in header.keys():
        alt = header['GPS GPSAltitude'].values[0]
        altitude = alt.num/alt.den
        if header['GPS GPSAltitudeRef'] == 1: altitude *= -1
    else:
        altitude = 0

    return {"ALT":altitude, "LAT":latitude, "LONG":longitude}



def main():

    exif_dict = {}

    for file_name in sys.argv[1:]:
        with open(file_name, "rb") as fp:
            #photo_data = fp.read()
            exif_dict[file_name] = grab_gps(fp)

    for file, metadata in exif_dict.items():
        print(file, end="\n")
        print(metadata, end="\n\n")

"""d
 TODO:
    - Create KML file of points (with title as photo file name and date in metadata if available)
    - Add extra info depending on metadata
        - Accuracy of reading
        - Altitude / Direction / Velocity
        - Destination?
        - Satelite used to calculate data
"""



if __name__=="__main__":
    main()