#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import scipy
import time
import rasterio
import geopandas as gpd
from pyproj import CRS
import xarray as xr

from RFSMHandler import *
from InputXML import *
from XYZ2Raster import *
from Meshgrid2Ascii import *

from IZCoast import izcoast
from RFSMManning import manning

from DiegoLibrary import asc2nc, crs_from_shp

################################################ MODIFICAR AQUÍ ######################################################################################
######################################################################################################################################################
# Dir general
mdt = "D:\RFSM\Casos_control\CFCC05\cfcc05_dem_a.asc" # Directorio completo
flood_case = "storm_dyn"  # 'storm_sta' or 'storm_dyn'
alpha = ""  # empty: no alpha / '_alpha1' or '_alpha2' or '_alpha3' or whatever alpha case you want to simulate

coast = "D:\RFSM\Casos_control\CFCC05\CFCC05_coast_A.shp" # Si indicas "coast", "buffer" quedará vacío y se generará desde "coast"
buffer = ""

lucascorine_tif = "D:\LucasCorine_30m_2019.tif" # Directorio completo

# Additional functionalities of the model
Rough_act = 1  # 1/0 to activate or not the variable manning roughness. If Rough_act = 0 a constant roughness (Input.ManningGlobalValue) is used
Levelout_act = 0  # 1/0 to activate or not drainage cells
River_act = 0  # 1/0 to activate or not the discharge point as if it were a river

format = "tiff" # tiff = result.tif / netcdf = result.nc

#######################################################################################################################################################

user = os.getcwd()
polygonize = fr"{user}\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\gdal_polygonize.py"
translate = fr"{user}\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\osgeo\gdal_translate.exe"

path_case = os.path.dirname(mdt)
control_case = os.path.splitext(os.path.basename(mdt))[0][0:6].upper()
option = os.path.splitext(os.path.basename(mdt))[0][-1].upper()

if not Rough_act:
    case_name = control_case + '_' + option + '_' + flood_case + alpha + "_man_cte"
else:
    case_name = control_case + '_' + option + '_' + flood_case + alpha + "_man_var"

mesh = os.path.splitext(os.path.basename(mdt))[0]
path_mesh = os.path.join(path_case,mesh)

crs_coast = crs_from_shp(coast)
epsg = crs_coast.to_epsg()

"""
Conversor de formato ASCII a formato TIFF
@input ASCII (.asc)
"""
def asc2tif(asc_in, epsg):

    print("ASCII to TIFF")
    tif_out = os.path.splitext(asc_in)[0]+".tif"
    args = f"{translate} -of \"GTiff\" {asc_in} {tif_out}"
    subprocess.call(args, stdout=None, stderr=None, shell=False)


    with rasterio.open(tif_out, 'r+') as f:
            f.crs = CRS.from_epsg(epsg)

    print("TIFF created")

    return tif_out


"""
Convierte un mapa ASC a NETCDF
"""
def asc2nc(asc_in, epsg):
    with rasterio.open(asc_in) as asc:
        data = asc.read(1)  # Lee la banda del raster

        # Obtén información necesaria del archivo ASC
        transform = asc.transform
        nodata = asc.nodata

        # Crea un objeto DataArray de xarray
        data_array = xr.DataArray(data, dims=('y', 'x'), coords={'x': asc.bounds.left + asc.res[0] * (0.5 + np.arange(asc.width)),
                                                                 'y': asc.bounds.top - asc.res[1] * (0.5 + np.arange(asc.height))})

        crs = CRS.from_epsg(epsg)

        # Agrega atributos a la variable
        data_array.attrs['transform'] = transform.to_gdal()
        data_array.attrs['crs'] = crs.to_string()
        data_array.attrs['_FillValue'] = nodata

        # Crea un conjunto de datos Dataset de xarray
        dataset = xr.Dataset({'data': data_array})

        nc_out = os.path.splitext(asc_in)[0] + ".nc"

        # Guarda el conjunto de datos en formato NetCDF
        dataset.to_netcdf(nc_out)

        print("NC created")

"""
Guarda en un fichero los parámetros usados para ejecutar RFSM
"""
def parameters2txt(file_txt):
    with open(file_txt, "w") as f:
        f.write(f"mdt = {mdt}\n")
        f.write(f"case_name = {case_name}\n")
        f.write(f"coast = {coast}\n")
        f.write(f"buffer = {buffer}\n")
        f.write(f"lucascorine_tif = {lucascorine_tif}\n")
        f.write(f"Rough_act = {Rough_act}\n")
        f.write(f"Levelout_act = {Levelout_act}\n")
        f.write(f"River_act = {River_act}\n")
        f.write(f"result_format = {format}\n")
        f.write(f"polygonize_directorio = {polygonize}\n")
        f.write(f"translate_directorio = {translate}\n")


def main_RFSM():
    # Genera IZCoasts
    izcoast.listIZCoast(mdt, coast, buffer, polygonize)

    # Genera Manning
    manning.generation_manning_file(mdt, lucascorine_tif, polygonize, epsg)

    # Add RFSM-EDA
    path_site = os.path.join(path_case, 'RFSM-results', mesh)
    if not os.path.exists(path_site):
        os.makedirs(path_site)

    path_site_case = os.path.join(path_site, case_name)
    if not os.path.exists(path_site_case):
        os.makedirs(path_site_case)
    else:
        shutil.rmtree(path_site_case)

    path_test = os.path.join(path_site_case, 'tests')
    if not os.path.exists(path_test):
        os.makedirs(path_test)

    path_csv = os.path.join(path_site_case, 'csv')
    if not os.path.exists(path_csv):
        os.makedirs(path_csv)

    path_inputs = os.path.join(path_case, 'input_dynamics')
    if not os.path.exists(path_inputs):
        os.makedirs(path_inputs)


    # Copiamos de la carpeta de la malla en la carpeta RFSM-results (sites) los archivos que lee RFSM
    shutil.copy(os.path.join(path_mesh, 'IZCoast_correg.txt'), path_site_case)
    shutil.copy(os.path.join(path_mesh, 'tblCell.csv'), path_csv)
    shutil.copy(os.path.join(path_mesh, 'tblImpactZone.csv'), path_csv)
    shutil.copy(os.path.join(path_mesh, 'tblIZNbrWidth.csv'), path_csv)
    shutil.copy(os.path.join(path_mesh, 'tblIZNeighbour.csv'), path_csv)
    shutil.copy(os.path.join(path_mesh, 'tblIZVolume.csv'), path_csv)
    shutil.copy(os.path.join(path_mesh, 'tblParameters.csv'), path_csv)

    # Eventos que vamos a simular
    evento_label = ['CFCC']  # ['Gloria', 'PMVE', 'TR5', 'TR10', 'TR25', 'TR50', 'TR100', 'TR500']
    cont = 1

    tic = time.time()

    for evento in evento_label:

        # BUILD CASE
        path_project = path_test
        RFSMH = RFSMHandler(path_project)
        
        # AccData files
        path_AccDataFiles = path_csv
        RFSMH.SetAccData(path_AccDataFiles)

        
        # SET BOUNDARY CONDITIONS
        cont += 1
        BCSetID = cont
        bc1 = scipy.io.loadmat(os.path.join(path_inputs, 'Input_RFSM_' + flood_case + '_' + option + alpha + '.mat'))
        PointList1 = bc1['input']
        IzListFile1 = os.path.join(path_site_case, 'IZCoast_correg.txt')
        BCTypeID1 = 2  # 1 overtopping; 2 level; 10 river or wadi discharge (raw inflow)
        LevelOutCond1 = 0  # 1 si es overtopping; 0 si es level/nivel o discharge
        RFSMH.AddBCSetFromIZList(BCSetID, IzListFile1, PointList1, BCTypeID1, LevelOutCond1)
        
        # Manning roughness
        # To introduce a variable roughness
        if Rough_act == 1:
            shutil.copy(os.path.join(path_mesh, 'CManning.mat'), path_site_case)
            mc = scipy.io.loadmat(os.path.join(path_site_case, 'CManning.mat'))
            CManningList = mc
            RFSMH.SetCManningList(BCSetID, CManningList)
        
        Input = InputXML()

        # Execution parameters
        Input.TestID = cont
        Input.TestDesc = f'ID{cont}'
        Input.BCSetID = cont
        Input.StartTime = '0#h'
        Input.EndTime = '12#h'
        # Input.EndTime = list_to_str([len(PointList1[0].inflowV), 'h'])  # Uncomment this line if PointList1 is defined
        Input.TimeStep = 1
        Input.SaveTimeStep = '1#h'
        Input.MaxTimeStep = 20
        Input.MinTimeStep = 0.01
        Input.AlphaParameter = 0.8
        Input.ManningGlobalValue = 0.15
        Input.Results = '1'
        Input.LogVerbose = '0'


        batch_mode = 1  # batch execution mode
        RFSMH.LaunchRFSM(Input, batch_mode)

        # RESULTS ascii
        export_mat = os.path.join(path_test, f'{case_name}.mat')
        RFSMH.Export2mat(export_mat, Input.TestID)

        # Cargar archivo .mat
        mf = scipy.io.loadmat(export_mat)

        # Crear ruta completa para el archivo de exportación
        f_export = os.path.join(path_test, f'{case_name}.asc')

        # Obtener los valores de x, y y level_max del archivo mat
        x = mf['x']
        y = mf['y']
        level_max = mf['level_max']

        XX, YY, ZZ = XYZ2Raster(x, y, level_max)
        Meshgrid2Ascii(f_export, XX, YY, ZZ, -9)

        if format == "tiff":
            new_tif = asc2tif(f_export,epsg)
        else:
            new_nc = asc2nc(f_export,epsg)

        toc = time.time()
        print("Elapsed Time:", toc-tic)


        parameters2txt(os.path.join(path_test,"parameters-RFSM.txt"))

        print(f"################## {case_name} executed #####################")



if __name__ == "__main__":
    main_RFSM()