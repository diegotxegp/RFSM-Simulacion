#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import geopandas as gpd
import numpy as np
import pandas as pd
import subprocess
import os
import time
import os.path as path

from main_RFSM_CFCC import mdt, coast, buffer, izmin, izmax, smalleriz, path_case, polygonize_directorio

############################################# MODIFICAR AQUÍ #################################################################################
#####################################################################################################################################################################################
directorio_cfcc = path_case
polygonize_directorio = polygonize_directorio

mdt = mdt
coast = coast # Si indicas "coast", "buffer" quedará vacío y se generará desde "coast"
buffer = buffer
izmin = izmin
izmax = izmax
smalleriz = smalleriz
#####################################################################################################################################################################################


directorio_dem = f"{directorio_cfcc}\{os.path.splitext(mdt)[0]}" # Sacar nombre que daremos a la nueva carpeta donde se guardarán los ficheros a partir del nombre del mdt

cfcc = mdt[0:7].upper() # Nombre del directorio principal CFCC## donde están los ficheros base
res = mdt[-6:-4].upper() # Letra de la resolucion (A/B)

"""
Genera la malla de celdas irregulares izid2.
"""
def generateMesh_CFCC():
    FNULL = open(os.devnull, 'w') # use this if you want to suppress output to stdout from the subprocess
    accdata = r".\accdata.exe"
    dem = fr"{directorio_cfcc}\{mdt}"
    #command = [accdata, "irregular", "-izmin", str(izmin), "-izmax", str(izmax), "-smalleriz", str(smalleriz), "-noizid1", dem]
    args = f"{accdata} irregular -izmin {izmin} -izmax {izmax} -smalleriz {smalleriz} -noizid1 \"{dem}\""
    subprocess.call(args, stdout=FNULL, stderr=FNULL, shell=False)
    print("izid2.asc created")

"""
Genera el icBoundary del contorno de la malla.
"""
def extract_icBoundary_CFCC():
    start = time.time()
    pathfInput = f"{directorio_dem}\izid2.asc"
    pathfTopo = f"{directorio_cfcc}\{mdt}"
    hMax = 15
    hMin = 0
    #------------------------------------------------------------------------------#
    def fCross(rI, cI, ListXY):
        '''
        Solves cross IZ location:
        global parameters: dictIZ, dictMinH, noDataVal, IA, OA.
        '''
        if IA[rI][cI] == noDataVal:
            for xy in ListXY:
                izid = IA[rI+xy[1]][cI+xy[0]]
                h = TA[rI+xy[1]][cI+xy[0]]
                if izid != noDataVal and hMin <= h <= hMax and izid != OA[rI+xy[1]][cI+xy[0]]: # remove "and ..." for cell face count
                    OA[rI+xy[1]][cI+xy[0]] = izid
                    try:
                        dictIZ[izid] += 1
                        dictMinH[izid] = min(dictMinH[izid], h)
                    except:
                        dictIZ[izid] = 1
                        dictMinH[izid] = h

    #------------------------------------------------------------------------------#

    # Create coast file and copy header
    fCoast = open(path.join(path.dirname(pathfInput),'icBoundary.asc'),'w')
    with open(pathfInput) as fInput:
        for i in range(6):
            fCoast.write(fInput.readline())

    # Read IZID file
    with open(pathfInput) as fInput, open(pathfTopo) as fTopo:
        ncols = int(fInput.readline().split()[1])
        nrows = int(fInput.readline().split()[1])
        for i in range(3):
            fInput.readline()
        noDataVal = int(fInput.readline().split()[1])
        for i in range(6):
            fTopo.readline()

        # Create arrays
        IA = [[[] for y in range(ncols)] for x in range(3)]
        TA = [[[] for y in range(ncols)] for x in range(3)]
        OA = [[noDataVal for y in range(ncols)] for x in range(3)]
        dictIZ = {}
        dictMinH = {}

        # 1st row
        IA[0][:] = list(map(int, fInput.readline().split()))
        IA[1][:] = list(map(int, fInput.readline().split()))

        TA[0][:] = list(map(float, fTopo.readline().split()))
        TA[1][:] = list(map(float, fTopo.readline().split()))

        fCross(0, 0, [(1, 0), (0, 1)])
        for nc in range(1, ncols-1):
            fCross(0, nc, [(1, 0), (0, 1), (-1, 0)])
        fCross(0, ncols-1, [(-1, 0), (0, 1)])

        # 2nd - nth row
        for nr in range(1, nrows-1):
            IA[2][:] = list(map(int, fInput.readline().split()))
            TA[2][:] = list(map(float, fTopo.readline().split()))

            fCross(1, 0, [(1, 0), (0, 1), (0, -1)])
            for nc in range(1, ncols-1):
                fCross(1, nc, [(1, 0), (-1, 0), (0, 1), (0, -1)])
            fCross(1, ncols-1, [(-1, 0), (0, 1), (0, -1)])
            fCoast.write(' '.join(str(r) for r in OA[0])+'\n')

            # Move Matrix up
            IA[0][:] = IA[1][:]
            IA[1][:] = IA[2][:]

            TA[0][:] = TA[1][:]
            TA[1][:] = TA[2][:]

            OA[0][:] = OA[1][:]
            OA[1][:] = OA[2][:]
            OA[2][:] = [noDataVal for y in range(ncols)]

            print("{0:.2f}%".format(100.0*nr/nrows))

        # nth row
        fCross(1, 0, [(1, 0), (0, -1)])
        for nc in range(1, ncols-1):
            fCross(1, nc, [(1, 0), (-1, 0), (0, -1)])
        fCross(1, ncols-1, [(-1, 0), (0, -1)])

        fCoast.write(' '.join(str(r) for r in OA[0])+'\n')
        fCoast.write(' '.join(str(r) for r in OA[1])+'\n')
        fCoast.close()

        print("{0:.2f}%".format(100.0))
        print("Writing Coast IZ list...".format(100.0))

        fizList = open(path.join(path.dirname(pathfInput),'listIZCoast.txt'),'w')
        fizList.write("{0}\t{1}\t{2}\n".format('IZID', 'nCells', 'minH'))
        for key in sorted(dictIZ.keys()):
            fizList.write("{0}\t{1}\t{2}\n".format(key, dictIZ[key], dictMinH[key]))
        fizList.close()

        print('Finished. It took {0:.2f} seconds.'.format(time.time()-start))

"""
Conversor de formato ascii (.asc) a formato shapefile (.shp)
"""
def asc_to_shp(asc,shp):

    print("asc to shp")

    command = ["python3", f"{polygonize_directorio}", asc, '-f', 'ESRI Shapefile', shp]
    subprocess.call(command)

    keep_spatial_reference(shp)

"""
Mantener el sistema de coordenadas
"""
def keep_spatial_reference(shp):

    # Guardamos el EPSG
    buffer_shp = gpd.read_file(f"{directorio_cfcc}\{buffer}")
    epsg = buffer_shp.crs

    shp_destino = gpd.read_file(shp)
    shp_destino.to_file(shp,crs=epsg)

"""
icBoundary + coast_buffer -> icCoast
"""
def icCoast_function():

    print("icCoast")

    icBoundary = gpd.read_file(f"{directorio_dem}\{cfcc}icBoundary{res}.shp")
    coast_buffer = gpd.read_file(f"{directorio_cfcc}\{buffer}")
    icCoast = icBoundary[icBoundary.geometry.intersects(coast_buffer.unary_union)]
    icCoast.to_file(f"{directorio_dem}\{cfcc}icCoast{res}.shp")


"""
izid2 + icCoast -> izCoast
"""
def izCoast_function():

    print("izCoast")

    izid2 = gpd.read_file(f"{directorio_dem}\{cfcc}izid2{res}.shp")
    icCoast = gpd.read_file(f"{directorio_dem}\{cfcc}icCoast{res}.shp")
    izCoast = izid2[izid2.geometry.overlaps(icCoast.unary_union)]
    izCoast.to_file(f"{directorio_dem}\{cfcc}izCoast{res}.shp")

"""
Cargar lista total "listIZCoast.txt" y seleccionar sólo las celdas costeras indicadas por "izCoast"
"""
def listIZCoast_function():

    print("listIZCoast")

    listIZCoast = np.loadtxt(f"{directorio_dem}\listIZCoast.txt", skiprows=1)
    izCoast = gpd.read_file(f"{directorio_dem}\{cfcc}izCoast{res}.shp")
    izCoast_df = pd.DataFrame(izCoast)
    izCoast_df = izCoast_df.drop_duplicates(subset="DN")
    izCoast_gridcode = izCoast_df.sort_values(by="DN")
    mascara = np.isin(listIZCoast[:, 0], izCoast_gridcode["DN"])
    listIZCoast_correg = listIZCoast[mascara]

    with open(f"{directorio_dem}\{cfcc}IZCoast_correg{res}.txt",'w') as f:
        for fila in listIZCoast_correg:
            linea = "\t".join(str(elemento) for elemento in fila)
            f.write(linea + "\n")

"""
Crea un buffer de una línea de costa
"""
def coast_to_buffer(coast):

    print("coast_to_buffer")

    # Devuelve la resolución desde el mdt
    def resolution(dem_asc):
        with open(dem_asc, 'r') as file:
            for line in file:
                if 'cellsize' in line:
                    # Elimina los espacios en blanco y divide la línea en palabras
                    words = line.strip().split()
                    resolucion = int(words[1])
                    return resolucion
                
    
    coastLine = fr"{directorio_cfcc}\{coast}"
    coastLine_gpd = gpd.read_file(coastLine)

    dem = fr"{directorio_cfcc}\{mdt}"
    resol = resolution(dem)
    
    coast_buffer = coastLine_gpd.buffer(resol)

    global buffer 
    buffer = f"{cfcc}coast_buffer{res}.shp"
    coast_buffer.to_file(f"{directorio_cfcc}\{buffer}")


def listIZCoast():
    
    print(cfcc+res)

    print("Loading...")

    # Si la linea de costa está indicada, se genera un buffer
    if coast != "":
        coast_to_buffer(coast)

    # Malla de celdas
    generateMesh_CFCC()

    # izid2.asc to izid2.shp
    asc_to_shp(f"{directorio_dem}\izid2.asc", f"{directorio_dem}\{cfcc}izid2{res}.shp")

    # icBoundary
    extract_icBoundary_CFCC()

    # icBoundary.asc to icBoundary.shp
    asc_to_shp(f"{directorio_dem}\icBoundary.asc", f"{directorio_dem}\{cfcc}icBoundary{res}.shp")


    icCoast_function()
    izCoast_function()
    listIZCoast_function()

    print("####################################### COMPLETED! #############################################")


if __name__ == "__main__":
    listIZCoast()
