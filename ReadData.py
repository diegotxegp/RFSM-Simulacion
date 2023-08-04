import csv
import numpy as np

def ReadData(csv_file):
    # Method for reading .csv files.
    # Returns table_header, table_data matrix

    print(f'Reading: {csv_file} ...')

    with open(csv_file, newline='') as csvfile:
        reader = csv.reader(csvfile)
        headerLine = next(reader)

        tableHeader = headerLine[0].split(', ')
        if len(tableHeader) == 1:
            tableHeader = headerLine[0].split(',')

        format_str = '%f ' * len(tableHeader)

        if tableHeader[0] == 'ParName':
            format_str = '%s %s'

        tableContent = np.loadtxt(csvfile, delimiter=',', dtype=format_str)

    print(' Done.')
    return tableHeader, tableContent