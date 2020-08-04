# pic2pin
OSINT script for scraping GPS metadata from images in bulk.

Supports KML, JSON and plaintext output to either stdout or a file

## Usage:
```
usage: pic2pin.py [-h] [-f {plain,json,kml}] [-a] [-r] [-o OUTPUT] [-v]
                  path [path ...]

positional arguments:
  path                  file or directory to process

optional arguments:
  -h, --help            show this help message and exit
  -f {plain,json,kml}, --format {plain,json,kml}
                        Choose output format
  -a, --address         Lookup addresses as well (requires network)
  -r, --recursive       Recurse into subdirectories
  -o OUTPUT, --output OUTPUT
                        Write output to file
  -v, --verbose         Prints progress bars (quiet by default)
```

## Examples:

Lookup addresses of coordinates found in all files in this directory and recurse down. Write as KML to a file.
```
pic2pin.py ./ -ravo out.kml --format kml
```

Scrape coordinates from  x.jpg and write as JSON to a file
```
pic2pin.py x.jpg --output out.json --format json
```

Lookup address and output to stdout as plaintext
```
pic2pin.py test/ireland.jpg -a

FILE: (md5) a71ded475134390bbcb3cf484ff88b94
        test/ireland.jpg
COORDINATES (lat, long):
        52.139276657230475, -10.274594797178132
ADDRESS:
        Harrington's Restaurant, Sráid na Trá, The Wood, Dingle ED, Kenmare Municipal District, County Kerry, Munster, V92 A091, Ireland
```

## Future

- matplotlib Basemap output
- report format output in pdf