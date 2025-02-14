from view_to_csv import ViewToCsvConvertor

def runTest(path_mapping,path_output):
    print('execution ' + path_mapping)
    ViewToCsvConvertor(path_mapping, path_output).execute()
    print('execution ' + path_mapping + '(old rml)')
    ViewToCsvConvertor(path_mapping, path_output, True).execute()

# csv view left join with json view
runTest('./test_cases/POCLV0001/mapping.ttl', './test_cases/POCLV0001/output/')
# json view left join with csv view
runTest('./test_cases/POCLV0002/mapping.ttl', './test_cases/POCLV0002/output/')
# csv view inner join with json view
runTest('./test_cases/POCLV0003/mapping.ttl', './test_cases/POCLV0003/output/')
# json field nested in csv file
runTest('./test_cases/POCLV0004/mapping.ttl', './test_cases/POCLV0004/output/')
# csv field nested in json file
runTest('./test_cases/POCLV0005/mapping.ttl', './test_cases/POCLV0005/output/')
# json field nesting to level 2
runTest('./test_cases/POCLV0006/mapping.ttl', './test_cases/POCLV0006/output/')

# use case telefonica
runTest('./use_cases/Telefonica/mapping.ttl', './use_cases/Telefonica/output/')



