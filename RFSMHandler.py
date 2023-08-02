#!/home/local/bin/python3
# -*- coding: utf-8 -*-

import os
import csv


class RFSMHandler:
    def __init__(self, path_project):
        # Initialize with project path
        self.path_src = os.path.abspath(__file__)
        
        if os.name == 'nt':  # Windows
            sf = 'Windows7_x86'
        elif os.name == 'posix':  # Unix-like
            sf = 'unix'
        else:
            sf = 'unknown'
        self.path_bin_RFSM = os.path.join(os.path.dirname(self.path_src), '..', '..', 'bin', 'RFSM', sf, 'RFSM_Hydrodynamic.exe')

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
        os.makedirs(self.path_input_accdata, exist_ok=True)
        os.replace(path_AccData, os.path.join(self.path_input_accdata, os.path.basename(path_AccData)))
        print(f'AccData tables copied from {path_AccData}')

    def LoadAccDataTables(self):
        # Load data from AccData csv tables
        dictParameters = self._read_csv(os.path.join(self.path_input_accdata, 'tblParameters.csv'))
        dictImpactCell = self._read_csv(os.path.join(self.path_input_accdata, 'tblCell.csv'))
        dictImpactZone = self._read_csv(os.path.join(self.path_input_accdata, 'tblImpactZone.csv'))

        # CSV files to matlab matrix
        self.m_tblCell = [
            dictImpactCell['CellID'], dictImpactCell['IZID'],
            dictImpactCell['GroundLevel'], dictImpactCell['MidX'], dictImpactCell['MidY']
        ]
        self.m_tblImpactZone = [
            dictImpactZone['IZID'], dictImpactZone['MinLevel'],
            dictImpactZone['NbCells'], dictImpactZone['MidX'], dictImpactZone['MidY'],
            dictImpactZone['IZTypeID'], dictImpactZone['FA_ID']
        ]
        self.m_tblParameters = [dictParameters['ParName'], dictParameters['ParValue']]

        # Boolean
        self.bool_AccDataLoaded = True

    def MakeInputUser(self):
        # Create Boundary Conditions input tables if they don't exist.
        if not os.path.exists(self.csv_tblkTestBCType):
            with open(self.csv_tblkTestBCType, 'w', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerow(['BCTypeID', 'BCType'])
                writer.writerow([1, 'Discharge'])
                writer.writerow([2, 'Level'])
                writer.writerow([3, 'LevelOut'])
                writer.writerow([4, 'Levelln'])
                writer.writerow([5, 'LevelFlowRating'])

        if not os.path.exists(self.csv_tusrBCFlowLevel):
            with open(self.csv_tusrBCFlowLevel, 'w', newline='') as fW:
                writer = csv.writer(fW)
                writer.writerow(['BCSetID', 'BCTypeID', 'IZID', 'Time', 'BCValue'])

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

    # ... (continue with the rest of the methods)
    
    def _read_csv(self, file_path):
        result = {}
        with open(file_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for key, value in row.items():
                    result.setdefault(key, []).append(float(value))
        return result