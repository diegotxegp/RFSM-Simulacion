#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil

################################################ MODIFICAR AQUÍ ######################################################################################
######################################################################################################################################################
# Dir general
path_main = r"D:\RFSM\Casos_control"
control_case = "CFCC08"
option = "A"
mdt = "cfcc08_dem_a.asc"
flood_case = "storm_dyn"  # 'storm_sta' or 'storm_dyn'
alpha = ""  # empty: no alpha / '_alpha1' or '_alpha2' or '_alpha3' or whatever alpha case you want to simulate

#######################################################################################################################################################

path_case = os.path.join(path_main, control_case)
mesh = os.path.splitext(mdt)[0]
path_mesh = os.path.join(path_case,mesh)
case_name = control_case + '_' + option + '_' + flood_case + alpha


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