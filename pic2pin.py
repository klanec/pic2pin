#!/usr/bin/env python3

import os
import sys
import argparse
import hashlib
import imghdr
import exifread
from geopy.geocoders import Nominatim
from tqdm import tqdm

import json
import simplekml


SUPPORTED = ['jpeg']


class FileReport(object):
    def __init__(self, digest, paths, geoloc=None):
        self.digest = digest
        self.paths = paths

        gps=grab_gps(paths[0])
        self.latitude=gps.get('latitude', None)
        self.longitude=gps.get('longitude', None)
        self.altitude=gps.get('altitude', None)
        self.address = ""

        if geoloc is not None and self.latitude is not None:
            try:
                self.address = geoloc.reverse(f"{self.latitude}, {self.longitude}").address
            except TypeError:
                pass
    
    
    def __str__(self):
        files = "\t" + "\n\t".join(self.paths)
        coords = "{}, {}".format(self.latitude, self.longitude)
        addr = '\nADDRESS:\n\t' + self.address + '\n' if self.address else ''
        output = "\nFILE: (md5) {d}\n{f}\nCOORDINATES (lat, long):\n\t{ll}{a}\n".format(
            d=self.digest,
            f=files,
            ll=coords,
            a=addr)
        return output



def parse_arguments():
    parser = argparse.ArgumentParser()
    supported_formats = ['plain', 'json', 'kml']
    # Positional
    parser.add_argument("path", 
                    help="file or directory to process",
                    nargs='+')
    # Formats
    parser.add_argument('-f', '--format', 
                    default=['plain'],
                    choices=supported_formats,
                    nargs=1,
                    help="Choose output format")
    # Optional
    parser.add_argument("-a", "--address", 
                    help="Lookup addresses as well (requires network)",
                    action="store_true")
    parser.add_argument("-i", "--ignore",
                    help="Exclude images without location data from the report",
                    action="store_true")
    parser.add_argument("-r", "--recursive", 
                    help="Recurse into subdirectories",
                    action="store_true")
    parser.add_argument("-o", "--output", 
                    help="Write output to file")
    parser.add_argument("-v", "--verbose", 
                    help="Prints progress bars (quiet by default)",
                    action="store_true")

    return vars(parser.parse_args())


def md5(fname):
    '''Take a path to a file and return the MD5 hash of the file as a hex string
    '''
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def is_valid_file(file):
    ''' Takes a path to a file and returns whether it is supported by pic2pin
    '''
    return imghdr.what(file) in SUPPORTED


def initialize_files(paths, recursive=False):
    '''Initialize and return the file dictionary in the format {md5(file):[paths]}

    Arguments:
        path: the FILE or DIRECTORY to initialize

    Keyword arguments:
        recursive: recurse into subdirectories (default is False)
    '''
    hashdict = {}
    if os.path.isdir(paths[0]) and len(paths) == 1:
        for root, _, files in os.walk(paths[0]):
            for f in files:
                full_path = os.path.join(root, f)
                if is_valid_file(full_path):
                    digest = md5(full_path)
                    if hashdict.get(digest):
                        hashdict[digest].append(full_path)
                    else:
                        hashdict[digest] = [full_path]
            if not recursive:
                break
    else:
        for path in paths:
            if is_valid_file(path):
                digest = md5(path)
                if hashdict.get(digest):
                    hashdict[digest].append(path)
                else:
                    hashdict[digest] = [path]
    return hashdict

    

def ifdtag_to_decimal(tag):
    '''Takes an exifread.classes.IfdTag, and converts the degrees-minutes-seconds GPS data to decimal
    '''
    degree = tag.values[0].num / tag.values[0].den
    minute = tag.values[1].num / tag.values[1].den / 60
    second = tag.values[2].num / tag.values[2].den / 3600
    return degree + minute + second


def grab_gps(file_path):
    '''Take a file path and return a dictionary of the GPS data as integers in a format as below:
    {
        'latitude' : I,
        'longitude': J,
        'altitude': K
    }

    Arguments:
        file_path --- the file to process

    Return:
        meta --- GPS data stripped from file and converted to decimal
    '''
    with open(file_path, "rb") as fd:
        header = exifread.process_file(fd, details=False)

    meta = {}
    lat_dms = header.get("GPS GPSLatitude")
    long_dms = header.get("GPS GPSLongitude")
    alt_tag = header.get("GPS GPSAltitude")

    if lat_dms and long_dms:
        latitude = ifdtag_to_decimal(lat_dms)
        longitude = ifdtag_to_decimal(long_dms)
        if header['GPS GPSLatitudeRef'].printable  == 'S': 
            latitude  *= -1
        if header['GPS GPSLongitudeRef'].printable == 'W': 
            longitude *= -1
        meta["longitude"] = longitude
        meta["latitude"] = latitude

    if alt_tag:
        alt_ratio = alt_tag.values[0]
        altitude = alt_ratio.num / alt_ratio.den
        if header['GPS GPSAltitudeRef'] == 1: 
            altitude *= -1
        meta["altitude"] = altitude

    return meta


def lookup_address(geoloc, lat, long):
    ''' Takes a geopy geolocator, a latitude and longitude as floats and looks up the associated address
    '''
    try:
        location = geoloc.reverse("{}, {}".format(lat, long))
        return location.address
    except TypeError:
        return "ADDRESS NOT FOUND"


def format_plain(reports):
    return "".join([r.__str__() for r in reports]) + "\n"


def format_json(reports):
    tmp = {i: vars(report) for i, report in enumerate(reports)}
    return json.dumps(tmp)


def format_kml(reports):
    kml = simplekml.Kml(open=1)
    for report in reports:
        pnt = kml.newpoint()
        pnt.name = report.digest
        pnt.description = ", ".join([os.path.basename(p) for p in report.paths])
        pnt.coords = [(report.longitude, report.latitude)]
    return kml.kml()

 
def main(path, format, address, ignore, recursive, output, verbose):
    '''TODO:
        - implement output
        - 
    '''
    reports = []
    geolocator = Nominatim(user_agent="pic2pin") if address else None
    init = initialize_files(path, recursive=recursive)

    for digest, paths in (tqdm(init.items()) if verbose else init.items()):
        file_report = FileReport(digest, paths, geoloc=geolocator)
        if ignore and not file_report.latitude and not file_report.longitude and not file_report.altitude:
            pass
        else:
            reports.append(file_report)
 
    # Switch for formatting
    out_str = {
        'plain' : format_plain,
        'json' : format_json,
        'kml' : format_kml
        #'pdf' : format_pdf
    }[format[0]](reports)

    if output:
        with open(output, "w") as wp:
            wp.write(out_str)
    else:
        print(out_str)


if __name__=='__main__':
    arguments = parse_arguments()

    #print(arguments)
    main(**arguments)