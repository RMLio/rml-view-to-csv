# RML-view-to-CSV

Proof-of-concept implementation for [RML Logical Views](https://github.com/kg-construct/rml-lv). 
For more information we refer to our [paper](https://biblio.ugent.be/publication/01J1YD9J9RBMKM1YC7VSSPASHM). 

## Prerequisites

The code is written and tested using Python 3.10.5. 
To install the needed libraries, run below command. 
```bash
pip install -r requirements.txt
```

## Use

The script takes as input an RML mapping and returns an equivalent mapping without logical views
(named `mapping_without_views.ttl` or `mapping_without_views_old_rml.ttl`)
All logical views are converted to logical sources with CSV files as source. 
These CSV files are the materialization of the original logical views. 
The new mapping file together with the original input data and the newly generated CSV files can be processed by any RML mapping engine that supports CSV source data. 

```
usage: view_to_csv.py [-h] [--version] [--mapping MAPPING] [--output_dir OUTPUT_DIR] [--old_rml] [--optimize] [--no_ref_object_map]

Copyright by (c) Els de Vleeschauwer (2024), available under the MIT license
options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --mapping MAPPING     The mapping file that needs to be converted.
  --output_dir OUTPUT_DIR
                        Directory to which the output is saved, default is "./"
  --old_rml             Enables the use of old RML namespaces and vocabulary in the resulting mapping file
  --optimize            Enables the optimization of the materialized logical view based on the triples maps
  --no_ref_object_map   Enables the replacement of referencing object maps by logical views
```

## Implemented features
- Flattening of nested data structures
- Handling of mixed data formats
- Extended joining of data sources  
- Field indexes

## Not implemented yet
- Templates and constants in Expression Fields
- Natural datatype mapping

## Supported data formats
- CSV 
- JSON

## Examples

Examples of mapping rules that can be handled with this implementation, can be found in the test cases and use cases.
- [Test cases](./test_cases)
- [Test cases from the RML Logical Views module](./test_cases_lv)
- [Use cases](./use_cases)

## COVERAGE of RML-LV TEST CASES
| Test Case ID      | Covered? |
|-------------------|----------|
| ./RMLLVTC0000a/   | True     |
| ./RMLLVTC0000b/   | True     |
| ./RMLLVTC0000c/   | True     |
| ./RMLLVTC0001a/   | True     |
| ./RMLLVTC0001b/   | False    |
| ./RMLLVTC0001c/   | False    |
| ./RMLLVTC0001d/   | True     |
| ./RMLLVTC0002a/   | True     |
| ./RMLLVTC0002b/   | True     |
| ./RMLLVTC0002c/   | True     |
| ./RMLLVTC0003a/   | True     |
| ./RMLLVTC0003b/   | True     |
| ./RMLLVTC0003c/   | True     |
| ./RMLLVTC0004a/   | False    |
| ./RMLLVTC0004b/   | False    |
| ./RMLLVTC0004c/   | False    |
| ./RMLLVTC0004d/   | False    |
| ./RMLLVTC0005a/   | True     |
| ./RMLLVTC0005b/   | True     |
| ./RMLLVTC0005c/   | True     |
| ./RMLLVTC0006a/   | True     |
| ./RMLLVTC0006b/   | True     |
| ./RMLLVTC0006c/   | True     |
| ./RMLLVTC0006d/   | True     |
| ./RMLLVTC0006e/   | True     |
| ./RMLLVTC0006f/   | True     |
| ./RMLLVTC0007a/   | True     |
| ./RMLLVTC0007b/   | True     |
| ./RMLLVTC0007c/   | True     |
| ./RMLLVTC0008a/   | True     |
| ./RMLLVTC0008b/   | True     |
| ./RMLLVTC0008c/   | True     |


