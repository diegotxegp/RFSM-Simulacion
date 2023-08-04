import csv

def Read2Container(path):
        # Method for reading .csv files.
        # Returns dictionary with csv header-column
        
        print(f'Reading: {path} ...')
        
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            tableHeader = next(reader)
            tableHeader = list(map(str.strip, tableHeader))

            tableContent = [[] for _ in range(len(tableHeader))]

            for fila in reader:
                for i in range(len(fila)):
                    tableContent[i].append(fila[i])

        
        # Create Dictionary (container)
        container = dict(zip(tableHeader, tableContent))
        
        print('Done.')
        return container