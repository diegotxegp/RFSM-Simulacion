#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import geopandas as gpd
import numpy as np
import pandas as pd
import subprocess
import os
import time

from DiegoLibrary import resolution_asc


directorio_cfcc = None
polygonize_directorio = None

mdt = None
coast = None # Si indicas "coast", "buffer" quedará vacío y se generará un nuevo buffer desde la linea marcada por "coast"
buffer = None
res_ref = 25
izmin = 20000
izmax = 40000
smalleriz = 10000

directorio_dem = None
cfcc = None
opt = None


"""
Constructor de variables globales
"""
def init(mdt1, coast1, buffer1, polygonize_directorio1):

    global directorio_cfcc, polygonize_directorio, mdt, coast, buffer, directorio_dem, cfcc, opt

    mdt = mdt1

    directorio_cfcc = os.path.dirname(mdt)
    polygonize_directorio = polygonize_directorio1

    coast = coast1 # Si indicas "coast", "buffer" quedará vacío y se generará desde "coast"
    buffer = buffer1
    

    directorio_dem = os.path.splitext(mdt)[0] # Sacar nombre que daremos a la nueva carpeta donde se guardarán los ficheros a partir del nombre del mdt

    cfcc = os.path.basename(mdt)[0:7].upper() # Nombre del directorio principal CFCC## donde están los ficheros base
    opt = os.path.basename(mdt)[-5:-4].upper() # Letra de la resolucion (A/B)

"""
Asigna el tamaño de las IZ según la resolución
"""
def iz_size(asc_in):

    res = resolution_asc(asc_in)

    izmin_out = res*izmin/res_ref
    izmax_out = res*izmax/res_ref
    smalleriz_out = res*smalleriz/res_ref

    return res, izmin_out, izmax_out, smalleriz_out

"""
Genera la malla de celdas irregulares izid2.
"""
def generateMesh_CFCC():
    FNULL = open(os.devnull, 'w') # use this if you want to suppress output to stdout from the subprocess
    accdata = r".\IZCoast\accdata.exe"
    #command = [accdata, "irregular", "-izmin", str(izmin), "-izmax", str(izmax), "-smalleriz", str(smalleriz), "-noizid1", dem]

    res,izmin,izmax,smalleriz = iz_size(mdt)

    args = f"{accdata} irregular -izmin {izmin} -izmax {izmax} -smalleriz {smalleriz} -noizid1 \"{mdt}\""
    subprocess.call(args, stdout=FNULL, stderr=FNULL, shell=False)
    print("izid2.asc created")

"""
Genera el icBoundary del contorno de la malla.
"""
def extract_icBoundary_CFCC():
    start = time.time()
    pathfInput = f"{directorio_dem}\izid2.asc"
    pathfTopo = mdt
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
    fCoast = open(os.path.join(os.path.dirname(pathfInput),'icBoundary.asc'),'w')
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

        fizList = open(os.path.join(os.path.dirname(pathfInput),'listIZCoast.txt'),'w')
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
    buffer_shp = gpd.read_file(buffer)
    epsg = buffer_shp.crs

    shp_destino = gpd.read_file(shp)
    shp_destino.to_file(shp,crs=epsg)

"""
icBoundary + coast_buffer -> icCoast
"""
def icCoast_function():

    print("icCoast")

    icBoundary = gpd.read_file(f"{directorio_dem}\{cfcc}icBoundary{opt}.shp")
    coast_buffer = gpd.read_file(buffer)
    icCoast = icBoundary[icBoundary.geometry.intersects(coast_buffer.unary_union)]
    icCoast.to_file(f"{directorio_dem}\{cfcc}icCoast{opt}.shp")


"""
izid2 + icCoast -> izCoast
"""
def izCoast_function():

    print("izCoast")

    izid2 = gpd.read_file(f"{directorio_dem}\{cfcc}izid2{opt}.shp")
    icCoast = gpd.read_file(f"{directorio_dem}\{cfcc}icCoast{opt}.shp")
    izCoast = izid2[izid2.geometry.overlaps(icCoast.unary_union)]
    izCoast.to_file(f"{directorio_dem}\{cfcc}izCoast{opt}.shp")

"""
Cargar lista total "listIZCoast.txt" y seleccionar sólo las celdas costeras indicadas por "izCoast"
"""
def listIZCoast_function():

    print("listIZCoast")

    listIZCoast = np.loadtxt(f"{directorio_dem}\listIZCoast.txt", skiprows=1)
    izCoast = gpd.read_file(f"{directorio_dem}\{cfcc}izCoast{opt}.shp")
    izCoast_df = pd.DataFrame(izCoast)
    izCoast_df = izCoast_df.drop_duplicates(subset="DN")
    izCoast_gridcode = izCoast_df.sort_values(by="DN")
    mascara = np.isin(listIZCoast[:, 0], izCoast_gridcode["DN"])
    listIZCoast_correg = listIZCoast[mascara]

    with open(f"{directorio_dem}\IZCoast_correg.txt",'w') as f:
        for fila in listIZCoast_correg:
            linea = "\t".join(str(elemento) for elemento in fila)
            f.write(linea + "\n")


"""
Crea un buffer de una línea de costa
"""
def coast_to_buffer(coastLine):

    print("coast_to_buffer")

    coastLine_gpd = gpd.read_file(coastLine)

    resol = resolution_asc(mdt)
    
    coast_buffer = coastLine_gpd.buffer(resol)

    global buffer 
    buffer = os.path.join(directorio_cfcc,f"{cfcc}coast_buffer{opt}.shp")
    coast_buffer.to_file(buffer)


def listIZCoast(mdt, coast, buffer, polygonize_directorio):

    init(mdt, coast, buffer, polygonize_directorio)
    
    print(cfcc+opt)

    print("Loading...")

    # Si la linea de costa está indicada, se genera un buffer
    if coast != "":
        coast_to_buffer(coast)

    # Malla de celdas
    generateMesh_CFCC()

    # izid2.asc to izid2.shp
    asc_to_shp(f"{directorio_dem}\izid2.asc", f"{directorio_dem}\{cfcc}izid2{opt}.shp")

    # icBoundary
    extract_icBoundary_CFCC()

    # icBoundary.asc to icBoundary.shp
    asc_to_shp(f"{directorio_dem}\icBoundary.asc", f"{directorio_dem}\{cfcc}icBoundary{opt}.shp")


    icCoast_function()
    izCoast_function()
    listIZCoast_function()

    print("####################################### COMPLETED! #############################################")
