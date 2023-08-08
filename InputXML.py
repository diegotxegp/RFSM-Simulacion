class InputXML:
    def __init__(self):
        self.TestID = None
        self.TestDesc = None
        self.BCSetID = None
        self.StartTime = '0'
        self.EndTime = '3600'
        self.TimeStep = '5'
        self.SaveTimeStep = '300'
        self.MaxTimeStep = '20'
        self.MinTimeStep = '0.01'
        self.AlphaParameter = '0.8'
        self.ManningGlobalValue = '0.05'
        self.ModelType = 'csv'
        self.DbName = None
        self.FA_ID = '1'
        self.TimeStepMethod = 'a'
        self.LogVerbose = '0'
        self.Results = '1|2|3'

    def write(self, path_xml):
        # Writes .xml file
        with open(path_xml, 'w') as fidW:
            fidW.write('<settings>\n')

            parameters = self.__dict__.keys()
            for param in parameters:
                value = getattr(self, param)
                value = str(value)
                fidW.write('<' + param + '>' + value + '</' + param + '>\n')

            fidW.write('</settings>')

        print(f'{path_xml} file created.')