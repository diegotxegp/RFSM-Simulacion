import os
import subprocess
import rasterio
from pyproj import CRS

from main_RFSM_CFCC import translate_directorio

translate_directorio = translate_directorio

"""
Conversor de formato ASCII a formato TIFF
@input ASCII (.asc)
"""
def asc2tif(asc_in, epsg):

    print("ASCII to TIFF")
    tif_out = os.path.splitext(asc_in)[0]+".tif"
    args = f"{translate_directorio} -of \"GTiff\" {asc_in} {tif_out}"
    subprocess.call(args, stdout=None, stderr=None, shell=False)


    with rasterio.open(tif_out, 'r+') as f:
            f.crs = CRS.from_epsg(epsg)

    print("TIFF created")

    return tif_out