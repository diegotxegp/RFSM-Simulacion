#!/home/local/bin/python3
# -*- coding: utf-8 -*-

from osgeo import gdal

import geopandas as gpd
import numpy as np
import pandas as pd

import rasterstats

import os

import rasterio
from rasterio.mask import mask

import subprocess

from pyproj import CRS


manning_directorio = None
cfcc = None
opcion = None
mdt = None
lucascorine_tif = None
EPSG = None

polygonize_directorio = None

cfcc_directorio = None
path_mesh = None
lucascorine = None
dem = None


"""
Constructor de varibles globales
"""
def init(path_main1, control_case1, option1, mdt1, lucascorine_tif1, polygonize_directorio1, EPSG1):

    global manning_directorio, cfcc, opcion, mdt, EPSG, polygonize_directorio, cfcc_directorio, path_mesh, lucascorine, dem

    manning_directorio = path_main1
    cfcc = control_case1
    opcion = option1
    mdt = mdt1
    lucascorine_tif = lucascorine_tif1
    EPSG = EPSG1

    polygonize_directorio = polygonize_directorio1


    cfcc_directorio = os.path.join(manning_directorio, cfcc)

    mesh = f"{cfcc.lower()}_dem_{opcion.lower()}"
    path_mesh = os.path.join(cfcc_directorio, mesh)

    lucascorine = os.path.splitext(os.path.basename(lucascorine_tif))[0]

    dem = os.path.join(manning_directorio, cfcc, mdt)


"""
Conversor de formato ascii (.asc) a formato shapefile (.shp)
"""
def asc_to_shp(asc_in):        

    print("ASC to SHP")

    shp_out = os.path.splitext(asc_in)[0]+".shp"

    command = ["python3", f"{polygonize_directorio}", asc_in, '-f', 'ESRI Shapefile', shp_out]
    subprocess.call(command)

    shp_destino = gpd.read_file(shp_out)
    shp_destino.to_file(shp_out,crs=CRS.from_epsg(EPSG))

    return shp_out


"""
Devuelve la resolución desde el mdt
"""
def resolution(dem_asc):
    with open(dem_asc, 'r') as file:
        for line in file:
            if 'cellsize' in line:
                # Elimina los espacios en blanco y divide la línea en palabras
                words = line.strip().split()
                resolucion = int(words[1])
                return resolucion

"""
Recorta la imagen tiff acorde al área indicada
"""
def extract_by_mask(tif_in, shp_in):
    # Abre el archivo raster y el archivo shapefile
    tif = rasterio.open(tif_in)
    shp = gpd.read_file(shp_in)

    # Obtén la geometría de la máscara del shapefile
    mask_geometry = shp.geometry.unary_union

    # Recorta el archivo raster utilizando la geometría del shapefile como máscara
    cropped_image, cropped_transform = mask(tif, [mask_geometry], crop=True)

    # Actualiza los metadatos del archivo raster recortado
    cropped_meta = tif.meta.copy()
    cropped_meta.update({
        'transform': cropped_transform,
        'height': cropped_image.shape[1],
        'width': cropped_image.shape[2]
    })

    # Guarda el resultado en un archivo TIFF
    lucascorine_out = f"{lucascorine}_masked.tif"
    tif_out = os.path.join(cfcc_directorio, lucascorine_out)
    with rasterio.open(tif_out, 'w', **cropped_meta) as dst:
        dst.write(cropped_image)

    # Cierra los datasets
    tif.close()
    shp = None

"""
Resample
"""
def resample(tif_in, res):
    # Abrir el archivo de entrada
    dataset = gdal.Open(tif_in)

    # Obtener información de la banda
    banda = dataset.GetRasterBand(1)
    nodata_value = banda.GetNoDataValue()

    # Crear una copia del archivo de entrada con la nueva resolución
    tif_out = os.path.splitext(tif_in)[0]+f"_{res}.tif"
    gdal.Warp(tif_out, dataset, xRes=res, yRes=res, dstNodata=nodata_value, resampleAlg=gdal.GRIORA_Bilinear)

    # Cerrar el dataset
    dataset = None

    print("Resolution changed")


"""
Por cada celda, consigue el tipo de suelo predominante
"""
def zonal_statistics_as_table(shp_in, tif_in):

    zones = gpd.read_file(shp_in)

    stats = rasterstats.zonal_stats(zones, tif_in, stats=["count", "majority"])

    results = []

    # Itera por cada estadística
    for i, stat in enumerate(stats):
        
        gridcode = zones.loc[i, "DN"]

        count = stat["count"]

        majority = stat["majority"]

        results.append({"gridcode": gridcode, "count": count, "majority": majority})

    df = pd.DataFrame(results)

    # Ordena por "gridcode"
    df = df.sort_values("gridcode")

    txt_out = fr"{cfcc_directorio}\{cfcc}_LandUseTable_{opcion}.txt"

    df.to_csv(txt_out, index=False, sep="\t")

"""
A cada celda, se le asigna un tipo de rugosidad de suelo
"""
def manning_roughness_coefficient():

    # Reading land use table and extracting only the information we want
    file_landuse = os.path.join(cfcc_directorio, f'{cfcc}_LandUseTable_{opcion}.txt')
    landuse_original = pd.read_csv(file_landuse, delimiter='\t').values
    landuse = landuse_original[:, [0, 2]]

    psave = os.path.join(path_mesh, 'landuse.txt')
    np.savetxt(psave, landuse, fmt='%d')

    # Reading the centroids file and extracting only the information we want
    file_centroids = os.path.join(path_mesh, 'tblImpactZone.csv')
    centroids_original = pd.read_csv(file_centroids)
    centroids = centroids_original[[' MidX', ' MidY', 'IZID']]

    psave = os.path.join(path_mesh, 'centroids.csv')
    centroids_df = pd.DataFrame(centroids)
    centroids_df.to_csv(psave, header=False, index=False, sep=',')

    # TRANSFORM LAND USE TYPE INTO MANNING ROUGHNESS
    centroids = pd.read_csv(os.path.join(path_mesh, 'centroids.csv'), delimiter=',', header=None)
    landuse = np.loadtxt(os.path.join(path_mesh, 'landuse.txt'))
    m = centroids

    # Se añade "majority" como cuarta columna
    m['']=landuse[:,1]

    s1 = np.where(m.iloc[:, 3] == 1)[0]  # urban area
    s2 = np.where((m.iloc[:, 3] >= 2) & (m.iloc[:, 3] <= 8))[0]  # other urban area
    s3 = np.where((m.iloc[:, 3] >= 9) & (m.iloc[:, 3] <= 15))[0]  # rural area
    s4 = np.where((m.iloc[:, 3] >= 16) & (m.iloc[:, 3] <= 21))[0]  # natural vegetation
    s5 = np.where((m.iloc[:, 3] >= 22) & (m.iloc[:, 3] <= 26))[0]  # beaches, dunes, sand and bare areas
    s6 = np.where((m.iloc[:, 3] >= 27) & (m.iloc[:, 3] <= 33))[0]  # waterbodies

    m.iloc[s1, 3] = 1
    m.iloc[s2, 3] = 2
    m.iloc[s3, 3] = 3
    m.iloc[s4, 3] = 4
    m.iloc[s5, 3] = 5
    m.iloc[s6, 3] = 6
    

    # Definition of land use types selected
    clases = [1, 2, 3, 4, 5, 6]

    # Definition of roughness associated to each type of land use
    man = [0.15, 0.2, 0.127, 0.1, 0.12, 0.05]

    manning = np.column_stack((m.iloc[:, 2], np.zeros(len(m))))
    for i in range(len(clases)):
        posi = np.where(m.iloc[:, 3] == clases[i])[0]
        if len(posi) > 0:
            manning[posi, 1] = man[i]

    # Save the results
    np.savetxt(os.path.join(path_mesh, 'CoefManning.dat'), manning, fmt='%.3f')

    # INPUT RFSM-EDA - MANNING ROUGHNESS
    ManningCoef = np.loadtxt(os.path.join(path_mesh, 'CoefManning.dat'))
    CManningList = []

    for k in range(len(ManningCoef)):
        iz_list = ManningCoef[k, 0]
        iz_cmanning = ManningCoef[k, 1]
        CManningList.append({'IZList': iz_list, 'IZCManning': iz_cmanning})

    np.save(os.path.join(path_mesh, 'CManning.npy'), CManningList)




def generation_manning_file(path_main, control_case, option, mdt, lucascorine_tif, polygonize_directorio, EPSG):

    init(path_main, control_case, option, mdt, lucascorine_tif, polygonize_directorio, EPSG)
    res = resolution(dem)
    cfcc_shp = asc_to_shp(dem)
    extract_by_mask(lucascorine_tif, os.path.join(cfcc_directorio, cfcc_shp))
    resample(os.path.join(cfcc_directorio,f"{lucascorine}_masked.tif"), res)
    zonal_statistics_as_table(os.path.join(path_mesh,f"{cfcc}_izid2_{opcion}.shp"), os.path.join(cfcc_directorio,f"{lucascorine}_masked_{res}.tif"))
    manning_roughness_coefficient()
