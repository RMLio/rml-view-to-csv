from view_to_csv import ViewToCsvConvertor

def runTests():
    ViewToCsvConvertor('./use_cases/Telefonica/mapping.ttl', './use_cases/Telefonica/output/', True).execute()
runTests()




