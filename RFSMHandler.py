#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import os
import shutil
import csv
import numpy as np
import scipy.io as sio
import subprocess

from ReadData import *

class RFSMHandler:
    def __init__(self, path_project):
        # Initializes with project path
        
        # Source and binary paths
        self.path_src = os.path.abspath(__file__)

        if os.name == 'nt':
            sf = 'Windows7_x86'
        elif os.name == 'posix':
            sf = 'unix'

        self.path_bin_RFSM = os.path.join(os.path.dirname(self.path_src), 'bin', 'RFSM', sf, 'RFSM_Hydrodynamic.exe')
        self.path_bin_RFSM.replace("\\","\\\\")

        # Project paths
        self.path_project = path_project
        self.path_input_user = os.path.join(path_project, 'Input_User')
        self.path_input_accdata = os.path.join(path_project, 'Input_AccData')
        self.path_input_xml = os.path.join(path_project, 'Input_xml')
        self.path_logs = os.path.join(path_project, 'log')
        self.path_export = os.path.join(path_project, 'export')

        # User input csv files
        self.csv_tusrBCFlowLevel = os.path.join(self.path_input_user, 'tusrBCFlowLevel.csv')
        self.csv_tblkTestBCType = os.path.join(self.path_input_user, 'tblkTestBCType.csv')

        self.csv_tusrBCRainfallZones = os.path.join(self.path_input_user, 'tusrBCRainfallZones.csv')
        self.csv_tusrBCRainfallRunoff = os.path.join(self.path_input_user, 'tusrBCRainfallRunoff.csv')

        self.csv_tusrIZManning = os.path.join(self.path_input_user, 'tusrIZManning.csv')

        # Booleans
        self.bool_AccDataLoaded = False

        # Build missing folders
        self.BuildFolders()

    def BuildFolders(self):
        # Build folders

        if not os.path.exists(self.path_project):
            os.makedirs(self.path_project)
            print(f'{self.path_project} made.')

        # subfolders
        subfs = [self.path_input_user, self.path_input_accdata, self.path_input_xml, self.path_logs, self.path_export]

        for subf in subfs:
            if not os.path.exists(subf):
                os.makedirs(subf)
                print(f'{subf} made.')


    def SetAccData(self, path_AccData):
        # Set project AccData files

        if os.path.exists(self.path_input_accdata):
            shutil.rmtree(self.path_input_accdata)
        
        shutil.copytree(path_AccData, self.path_input_accdata)
        print(f'AccData tables copied from {path_AccData}')

    def LoadAccDataTables(self):
        # Load data from AccData csv tables

        tableHeader, tableContent = ReadData(os.path.join(self.path_input_accdata, 'tblParameters.csv'))
        dictParameters = dict(zip(tableHeader, tableContent))
        tableHeader, tableContent = ReadData(os.path.join(self.path_input_accdata, 'tblCell.csv'))
        dictImpactCell = dict(zip(tableHeader, tableContent))
        tableHeader, tableContent = ReadData(os.path.join(self.path_input_accdata, 'tblImpactZone.csv'))
        dictImpactZone = dict(zip(tableHeader, tableContent))

        # CSV files to matlab matrix
        self.m_tblCell = list(zip(
            dictImpactCell['CellID'], dictImpactCell['IZID'],
            dictImpactCell['GroundLevel'], dictImpactCell['MidX'], dictImpactCell['MidY']
        ))

        self.m_tblImpactZone = list(zip(
            dictImpactZone['IZID'], dictImpactZone['MinLevel'], dictImpactZone['NbCells'],
            dictImpactZone['MidX'], dictImpactZone['MidY'], dictImpactZone['IZTypeID'], dictImpactZone['FA_ID']
        ))

        self.m_tblParameters = list(zip(dictParameters['ParName'], dictParameters['ParValue']))

        # Boolean
        self.bool_AccDataLoaded = True

    def MakeInputUser(self):
        # Create Boundary Conditions input tables if them don't exist.

        if not os.path.exists(self.csv_tblkTestBCType):
            with open(self.csv_tblkTestBCType, 'w') as fW:
                fW.write('BCTypeID, BCType\n')
                fW.write('1, Discharge\n')
                fW.write('2, Level\n')
                fW.write('3, LevelOut\n')
                fW.write('4, Levelln\n')
                fW.write('5, LevelFlowRating\n')

        if not os.path.exists(self.csv_tusrBCFlowLevel):
            with open(self.csv_tusrBCFlowLevel, 'w') as fW:
                fW.write('BCSetID, BCTypeID, IZID, Time, BCValue\n')

    def CleanRainfall(self):
        # Clean Rainfall Conditions input tables

        if os.path.exists(self.csv_tusrBCRainfallZones):
            os.remove(self.csv_tusrBCRainfallZones)

        if os.path.exists(self.csv_tusrBCRainfallRunoff):
            os.remove(self.csv_tusrBCRainfallRunoff)

        with open(self.csv_tusrBCRainfallZones, 'w') as fW:
            fW.write('RainfallZoneID, Time, RainfallIntensity\n')

        with open(self.csv_tusrBCRainfallRunoff, 'w') as fW:
            fW.write('IZID, RainfallZoneID, RunoffCoef\n')

    def CleanRainfall(self):
        # Clean Rainfall Conditions input tables

        if os.path.exists(self.csv_tusrBCRainfallZones):
            os.remove(self.csv_tusrBCRainfallZones)

        if os.path.exists(self.csv_tusrBCRainfallRunoff):
            os.remove(self.csv_tusrBCRainfallRunoff)

        with open(self.csv_tusrBCRainfallZones, 'w', newline='') as fW:
            writer = csv.writer(fW)
            writer.writerow(['RainfallZoneID', 'Time', 'RainfallIntensity'])

        with open(self.csv_tusrBCRainfallRunoff, 'w', newline='') as fW:
            writer = csv.writer(fW)
            writer.writerow(['IZID', 'RainfallZoneID', 'RunoffCoef'])

    def AddBCSetFromIZList(self, BCSetID, IZListFile, PointList, BCTypeID, dolvlOut):
        # Set case BC Test from IZListFile by locating the nearest source point

        # IZListFile --> File with IZID IZncoastcells IZLevel

        # PointList = [Point1, Point2, ...]
        # Point1.XY = [PointXvalue, PointYvalue];
        # Point1.timeV = [t0, t1, t2, t3,...] (seconds);
        # Point1.inflowV = discharge [q0, q1, q2, q3,...]; or levels [l0, l1, l2, l3, ...]

        # BCTypeID --> 1 discharge, 2 level, 10 river discharge (TODO: CAMBIAR TRUCO POR NUEVA FUNCION)
        # dolvlOut --> 1 yes, 0 no

        raw_q = False
        if BCTypeID == 10:
            BCTypeID = 1
            raw_q = True

        PointList = PointList[0]

        # Check Accdata is loaded
        if not self.bool_AccDataLoaded:
            self.LoadAccDataTables()

        if os.path.exists(self.csv_tusrBCFlowLevel):
            os.remove(self.csv_tusrBCFlowLevel)

        # Make user input csv tables if doesn't exist
        self.MakeInputUser()

        # Load IZListFile
        IzList = np.loadtxt(IZListFile)

        """# Check sets BCSetID-BCType-IZID is not already stored at csv_tusrBCFlowLevel
        BCFlowLevel = np.loadtxt(self.csv_tusrBCFlowLevel, delimiter=',')
        storedSets = np.unique(BCFlowLevel[:, :3], axis=0)
        newSets = np.column_stack((np.full(len(IzList), BCSetID), np.full(len(IzList), BCTypeID), IzList[:, 0]))

        if np.any(np.isin(newSets, storedSets, assume_unique=True, axis=0)):
            print('Error: BCSetID-BCType-IZID combination already exists in tusrBCFlowLevel.csv input file.')
            return"""

        # Add new testBC
        for izIndex in range(len(IzList)):
            IZID, IZncells, IZLevel = IzList[izIndex]

            # Get IZ coast length
            cellsize = self.m_tblParameters[0][1]
            IZLength = IZncells * float(cellsize)

            # Find IZ centroids
            MidX = [float(item[3]) for item in self.m_tblImpactZone if int(item[0]) == IZID]
            MidY = [float(item[4]) for item in self.m_tblImpactZone if int(item[0]) == IZID]

            # Find closest point to IZ centroid
            if len(PointList) == 1:
                ClosestPoint = PointList[0]
            else:
                DistVector = [np.sqrt((point["x"][0][0] - MidX)**2 + (point["y"][0][0] - MidY)**2) for point in PointList]

                posClosestPoint = np.argmin(DistVector)
                ClosestPoint = PointList[posClosestPoint]

            # Time data (seconds)
            Time = ClosestPoint['timeV']
            timeV = Time.tolist()[0]

            # Create testBCValueMatrix
            testBCValueMatrixIn = np.zeros((len(timeV), 5))
            testBCValueMatrixIn[:, 0] = BCSetID
            testBCValueMatrixIn[:, 1] = BCTypeID
            testBCValueMatrixIn[:, 2] = IZID
            testBCValueMatrixIn[:, 3] = timeV

            # Check if key restrict values are being repeated

            inflow = ClosestPoint['inflowV']
            inflowV = inflow.tolist()[0]

            # TODO: Add new BCTypeID ?
            if BCTypeID == 2:  # level
                testBCValueMatrixIn[:, 4] = inflowV - IZLevel
                testBCValueMatrixIn[testBCValueMatrixIn[:, 4] < 0, 4] = 0  # remove negative values

            elif BCTypeID == 1 and not raw_q:  # discharge (coast)
                testBCValueMatrixIn[:, 4] = inflowV * IZLength

            elif BCTypeID == 1 and raw_q:  # discharge (mountain. Use raw inflow value)
                testBCValueMatrixIn[:, 4] = inflowV

            # level out condition
            if dolvlOut == 1:
                auxlvlout = np.zeros((len(timeV), 5))
                auxlvlout[:, 0] = BCSetID
                auxlvlout[:, 1] = 3
                auxlvlout[:, 2] = IZID
                auxlvlout[:, 3] = Time
                auxlvlout[:, 4] = IZLevel

                testBCValueMatrixIn = np.concatenate((testBCValueMatrixIn, auxlvlout))

            print(f'{izIndex+1}/{len(IzList)} done.', end='\r')
            with open(self.csv_tusrBCFlowLevel, 'a', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerows(testBCValueMatrixIn)
    

    def SetLevelOut(self, BCSetID, IZListFile, timeV):
        # Set case BC Test from IZListFile by locating the nearest source point
        # BC Test is only level out with no inflow conditions

        # IZListFile --> File with IZID IZncoastcells IZLevel
        # timeV      --> [t0, t1, t2, t3,...] (seconds)

        # Load IZListFile
        IzList = np.loadtxt(IZListFile)

        # Make levelout testBCValueMatrix
        testBCValueMatrixIn = np.zeros((1, 5))
        for izIndex in range(len(IzList)):
            IZID, _, IZLevel = IzList[izIndex]

            auxlvlout = np.zeros((len(timeV), 5))
            auxlvlout[:, 0] = BCSetID
            auxlvlout[:, 1] = 3
            auxlvlout[:, 2] = IZID
            auxlvlout[:, 3] = timeV
            auxlvlout[:, 4] = IZLevel

            testBCValueMatrixIn = np.concatenate((testBCValueMatrixIn, auxlvlout))

        # Remove first row
        testBCValueMatrixIn = testBCValueMatrixIn[1:]

        print(f'100%', end='\n')
        with open(self.csv_tusrBCFlowLevel, 'a', newline='') as fW:
            writer = csv.writer(fW)
            writer.writerows(testBCValueMatrixIn)

    def SetCManningList(self, BCSetID, CManningList):
        # Set case CManning from CManningList

        # CManningList = [CManningZone1, CManningZone2, ...]
        # CManningList.IZList = [IZID1, IZID2, ...];
        # CManningList.IZCManning = [IZCManning1, IZCManning2, ...];

        # Make tusrIZManning if don't exist
        if not os.path.exists(self.csv_tusrIZManning):
            with open(self.csv_tusrIZManning, 'w', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerow(['BCSetID', 'IZID', 'CManning'])

        # CManning matrix
        TestCManning = np.empty((0, 3))
        for CMIndex in range(len(CManningList)):
            CManningToAdd = CManningList[CMIndex]

            for rowIndex in range(len(CManningToAdd['IZList'])):
                newRow = [BCSetID, CManningToAdd['IZList'][rowIndex], CManningToAdd['IZCManning'][rowIndex]]
                TestCManning = np.vstack((TestCManning, newRow))

        with open(self.csv_tusrIZManning, 'a', newline='') as fW:
            writer = csv.writer(fW)
            writer.writerows(TestCManning)

    def SetRainfall(self, RainFallZonesList):
        # Set case Rainfall from RainFallZones

        # RainFallZonesList = [RainFallZone1, RainFallZone2, ...]
        # RainFallZone.IZList = [IZID1, IZID2, ...];
        # RainFallZone.IZRunOffCoefList = [IZRuOffCoef1, IZRuOffCoef2, ...];
        # RainFallZone.timeV = [t0, t1, t2, t3,...];
        # RainFallZone.inflowV = [q0, q1, q2, q3,...];

        # Clean Rainfall input csvs
        self.CleanRainfall()

        # Set rainfall zones
        for rainFZIndex in range(len(RainFallZonesList)):
            RainFallZoneToAdd = RainFallZonesList[rainFZIndex]

            pos_end = min(len(RainFallZoneToAdd['timeV']), len(RainFallZoneToAdd['inflowV']))

            c1 = np.full(pos_end, rainFZIndex, dtype=int)
            c2 = np.array(RainFallZoneToAdd['timeV'][:pos_end])
            c3 = np.array(RainFallZoneToAdd['inflowV'][:pos_end])

            TestRainfallZonesfMatrix = np.column_stack((c1, c2, c3))

            # Append to file
            print(f'{100*rainFZIndex//len(RainFallZonesList)}%', end=' ')
            with open(self.csv_tusrBCRainfallZones, 'a', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerows(TestRainfallZonesfMatrix)

        for rainFZIndex in range(len(RainFallZonesList)):
            RainFallZoneToAdd = RainFallZonesList[rainFZIndex]

            pos_end = len(RainFallZoneToAdd['IZList'])

            c1 = np.array(RainFallZoneToAdd['IZList'][:pos_end])
            c2 = np.full(pos_end, rainFZIndex, dtype=int)
            c3 = np.array(RainFallZoneToAdd['IZRunOffCoefList'][:pos_end])

            TestRainfallRunoff = np.column_stack((c1, c2, c3))

            # Append to file
            print(f'{100*rainFZIndex//len(RainFallZonesList)}%', end=' ')
            with open(self.csv_tusrBCRainfallRunoff, 'a', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerows(TestRainfallRunoff)

    def RemoveBCSet(self, BCSetID):
        # Remove BCSetID from csv_tusrBCFlowLevel

        with open(self.csv_tusrBCFlowLevel, 'r') as fR:
            reader = csv.reader(fR)
            header = next(reader)

            BCFlowLevel = np.array([row for row in reader])

        to_remove = BCFlowLevel[:, 0] == str(BCSetID)

        if np.any(to_remove):
            filtered_data = BCFlowLevel[~to_remove]
            with open(self.csv_tusrBCFlowLevel, 'w', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerow(header)
                writer.writerows(filtered_data)

    def LaunchRFSM(self, inputxml, batchMode):
        # Creates input.xml and executes RFSM
        # inputxml is an instance of InputXML class
        # batchMode = True for batch simulation

        # Create input.xml file for current TestID
        path_xml = os.path.join(self.path_input_xml, f'input_{inputxml.TestID}.xml')

        inputxml.DbName = self.path_project
        inputxml.write(path_xml)

        # Execute current TestID
        exec_path = self.path_bin_RFSM

        b = ""

        if batchMode:
            b = "-b"

        cmd = [r'{}'.format(exec_path), b, path_xml]
        subprocess.call(cmd)

        """# Move log file
        execfolder = os.path.dirname(self.path_bin_RFSM)
        print(execfolder)
        logfiles = [f for f in os.listdir(execfolder) if f.endswith('.log')]
        print(logfiles)
        newest_logfile = max(logfiles, key=lambda f: os.path.getctime(os.path.join(execfolder, f)))

        org = os.path.join(execfolder, newest_logfile)
        dst = os.path.join(self.path_logs, f'TestID_{inputxml.TestID}.log')
        os.rename(org, dst)

        # Clean old log files
        for f in logfiles:
            os.remove(os.path.join(execfolder, f))"""


    def Export2mat(self, path_export_mat, TestID):
        # Export TestID results to .mat file (XYZ similar data)

        # Delete previous .mat file
        if os.path.exists(path_export_mat):
            os.remove(path_export_mat)

        # Check Accdata is loaded
        if not self.bool_AccDataLoaded:
            self.LoadAccDataTables()

        # Cell Parameters
        cell_izs = np.array([float(item[1]) for item in self.m_tblCell])
        cell_z_ground = np.array([float(item[2]) for item in self.m_tblCell])
        cell_x = np.array([float(item[3]) for item in self.m_tblCell])
        cell_y = np.array([float(item[4]) for item in self.m_tblCell])

        # Write cells topography to .mat file
        print(f'Writing: {path_export_mat} - topography XYZ data...', end='')
        data = {
            "x": cell_x.reshape(-1, 1),
            "y": cell_y.reshape(-1, 1),
            "z": cell_z_ground.reshape(-1, 1)
        }
        matf = sio.savemat(path_export_mat, data)
        print(' Done.')

        # Read output ResultsIZMax
        rf = os.path.join(self.path_project, f'Results_{TestID}', 'tusrResultsIZMax.csv')
        _, ResultsIZMax = ReadData(rf)

        # Solve Cells for ResultsIZMax
        cell_z_water_level_max = np.zeros(len(cell_izs))
        print(f'Writing: {path_export_mat} - level_max (tusrResultsIZMax) data...')
        for j in range(len(cell_izs)):
            cell_iz = cell_izs[j]

            z_ground_water = ResultsIZMax[ResultsIZMax[:, 1] == cell_iz, 2]
            if len(z_ground_water) > 0:
                cell_z_water_level_max[j] = max(z_ground_water - cell_z_ground[j], 0)
            else:
                cell_z_water_level_max[j] = np.nan

        cell_z_water_level_max[cell_z_water_level_max <= 0.001] = np.nan

        # Write cells max level results to .mat file
        matf['level_max'] = cell_z_water_level_max
        print(' Done.')

        # Read output ResultsIZTmp
        rf = os.path.join(self.path_project, f'Results_{TestID}', 'tusrResultsIZTmp.csv')
        _, ResultsIZTmp = csv.ReadData(rf)

        # Solve Cells for ResultsIZTmp
        cell_z_water_level_tmp = np.zeros(len(cell_izs))
        time_v = np.sort(np.unique(ResultsIZTmp[:, 1]))

        matf['level_time'] = time_v

        print(f'Writing: {len(time_v)} time fields...')
        for i in range(len(time_v)):
            time_instant = time_v[i]

            # time results
            tr = ResultsIZTmp[ResultsIZTmp[:, 1] == time_instant, :]
            izid_level = tr[:, [2, 4]]

            field_name = f'level_{i:04d}'
            print(f'Writing: {path_export_mat} - tmp: {field_name} (tusrResultsIZTmp) data...')
            for j in range(len(cell_izs)):
                cell_iz = cell_izs[j]

                z_ground_water = izid_level[izid_level[:, 0] == cell_iz, 1]
                if len(z_ground_water) > 0:
                    cell_z_water_level_tmp[j] = max(z_ground_water - cell_z_ground[j], 0)
                else:
                    cell_z_water_level_tmp[j] = np.nan
            cell_z_water_level_tmp[cell_z_water_level_tmp <= 0.001] = np.nan

            # Write cells max level results to .mat file
            matf[field_name] = cell_z_water_level_tmp
            print(' Done.')

        sio.savemat(path_export_mat, matf, appendmat=False)

    def GetIZFromPoint(self, xPointList, yPointList):
        # returns closest cell IZID for the point X,Y input coordinates
        CellIZID = []
        for i in range(len(xPointList)):
            dist_vector = np.sqrt((self.m_tblCell[:, 3] - xPointList[i])**2 + (self.m_tblCell[:, 4] - yPointList[i])**2)
            pos_closest_cell = np.argmin(dist_vector)

            ClosestCell = self.m_tblCell[pos_closest_cell]
            CellIZid = ClosestCell[1]
            CellIZID.append(CellIZid)

        return CellIZID
