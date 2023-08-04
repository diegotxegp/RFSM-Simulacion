import csv

def Read2Container(path):
        # Method for reading .csv files.
        # Returns dictionary with csv header-column
        
        print(f'Reading: {path} ...')
        
        with open(path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headerLine = next(reader)
        
        tableHeader = [header.strip() for header in headerLine]
        format = ['%f' for _ in tableHeader]
        
        if tableHeader[0] == 'ParName':
            format[0] = '%s'
        
        with open(path, newline='') as csvfile:
            tableContent = list(csv.reader(csvfile, delimiter=','))
            
        # Transpose tableContent to convert rows into columns
        tableContent = list(map(list, zip(*tableContent)))

        print(tableHeader)
        print(tableContent)
        
        # Convert the content to their respective formats
        tableContent = [list(map(eval, row)) for row in tableContent]
        
        # Create Dictionary (container)
        container = dict(zip(tableHeader, tableContent))
        
        print('Done.')
        return container