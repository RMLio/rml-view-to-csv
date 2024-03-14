from view_to_csv import ViewToCsvConvertor

def runTests():
    # csv view left join with json view
    ViewToCsvConvertor('./test_cases/POCLV0001/mapping.ttl', './test_cases/POCLV0001/output/').execute()
    # json view left join with csv view
    ViewToCsvConvertor('./test_cases/POCLV0002/mapping.ttl', './test_cases/POCLV0002/output/').execute()
    # csv view inner join with json view
    ViewToCsvConvertor('./test_cases/POCLV0003/mapping.ttl', './test_cases/POCLV0003/output/').execute()
    # csv view left join with json view old rml
    ViewToCsvConvertor('./test_cases/POCLV0001/mapping.ttl', './test_cases/POCLV0001/output_old_rml/', True).execute()
    # json view left join with csv view old rml
    ViewToCsvConvertor('./test_cases/POCLV0002/mapping.ttl', './test_cases/POCLV0002/output_old_rml/', True).execute()
    # csv view inner join with json view
    ViewToCsvConvertor('./test_cases/POCLV0003/mapping.ttl', './test_cases/POCLV0003/output_old_rml/', True).execute()
    # json field nested in csv file
    ViewToCsvConvertor('./test_cases/POCLV0004/mapping.ttl', './test_cases/POCLV0004/output/').execute()
    # csv field nested in json file
    ViewToCsvConvertor('./test_cases/POCLV0005/mapping.ttl', './test_cases/POCLV0005/output/').execute()
    # json field nesting to level 2
    ViewToCsvConvertor('./test_cases/POCLV0006/mapping.ttl', './test_cases/POCLV0006/output/').execute()
runTests()




