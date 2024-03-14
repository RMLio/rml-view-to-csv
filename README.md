# RML-view-to-CSV

Proof-of-concept implementation for [RML Logical Views](https://github.com/kg-construct/rml-lv). 
For more information we refer to our [paper](https://openreview.net/forum?id=ecukfSgXaR). 

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

## Supported data formats
- CSV 
- JSON

## Examples

Examples of mapping rules that can be handled with this implementation, can be found in the test cases and use cases.
- [Test cases](./test_cases): see mapping.ttl
- [Test cases from the RML Logical Views module](./test_cases_lv): see mapping_old_rml.ttl (converted to the old rml terms to enable processing with RMLMapper v6.5.1)
- [Use cases](./use_cases): see mapping.ttl


