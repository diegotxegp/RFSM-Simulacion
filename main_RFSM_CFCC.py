#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
import scipy
import time
import rasterio
from pyproj import CRS

from RFSMHandler import *
from InputXML import *
from XYZ2Raster import *
from Meshgrid2Ascii import *

from IZCoast import izcoast
from RFSMManning import manning

################################################ MODIFICAR AQUÍ ######################################################################################
######################################################################################################################################################
# Dir general
path_main = r"D:\RFSM\Casos_control"
control_case = "CFCC08"
option = "A"
mdt = "cfcc08_dem_a.asc"
flood_case = "storm_dyn"  # 'storm_sta' or 'storm_dyn'
alpha = ""  # empty: no alpha / '_alpha1' or '_alpha2' or '_alpha3' or whatever alpha case you want to simulate
EPSG = 3035

coast = "CFCC08_coast_A.shp" # Si indicas "coast", "buffer" quedará vacío y se generará desde "coast"
buffer = ""
izmin = 20000
izmax = 40000
smalleriz = 10000

lucascorine_tif = "D:\LucasCorine_30m_2019.tif"

polygonize_directorio = r'C:\Users\gprietod\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\Scripts\gdal_polygonize.py'
translate_directorio = r"C:\Users\gprietod\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages\osgeo\gdal_translate.exe"

#######################################################################################################################################################

path_case = os.path.join(path_main, control_case)
mesh = os.path.splitext(mdt)[0]
path_mesh = os.path.join(path_case,mesh)
case_name = control_case + '_' + option + '_' + flood_case + alpha

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

def main_RFSM():
    # Genera IZCoasts
    izcoast.listIZCoast(mdt, coast, buffer, izmin, izmax, smalleriz, path_case, polygonize_directorio)

    # Genera Manning
    manning.generation_manning_file(path_main, control_case, option, mdt, lucascorine_tif, polygonize_directorio, EPSG)

    # Add RFSM-EDA
    path_site = os.path.join(path_case, 'RFSM-results', mesh)
    if not os.path.exists(path_site):
        os.makedirs(path_site)

    path_site_case = os.path.join(path_site, case_name)
    if not os.path.exists(path_site_case):
        os.makedirs(path_site_case)

    path_test = os.path.join(path_site_case, 'tests')
    if not os.path.exists(path_test):
        os.makedirs(path_test)

    path_csv = os.path.join(path_site_case, 'csv')
    if not os.path.exists(path_csv):
        os.makedirs(path_csv)

    path_inputs = os.path.join(path_case, 'input_dynamics')
    if not os.path.exists(path_inputs):
        os.makedirs(path_inputs)

    # Additional functionalities of the model
    Rough_act = 0  # 1/0 to activate or not the variable manning roughness. If Rough_act = 0 a constant roughness (Input.ManningGlobalValue) is used
    Levelout_act = 0  # 1/0 to activate or not drainage cells
    River_act = 0  # 1/0 to activate or not the discharge point as if it were a river


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
            CManningList = mc['CManningList']
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
        Input.ManningGlobalValue = 0.05
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

        new_tif = asc2tif(f_export,EPSG)

        toc = time.time()
        print("Elapsed Time:", toc-tic)


if __name__ == "__main__":
    main_RFSM()