#! /bin/bash

#test -f ./rmlmapper-6.5.1-r371-all.jar || curl -LO https://github.com/RMLio/rmlmapper-java/releases/download/v6.5.1/rmlmapper-6.5.1-r371-all.jar

python ../view_to_csv.py --mapping $1/mapping_old_rml.ttl --output_dir $1/output --old_rml
# replaced by rmlmapper.jar from dev branch, because rmlmapper v6.5.1 doesn't seem to recognize null value at end of CSV line.
java -jar ./rmlmapper.jar -m $1/output/mapping_without_views_old_rml.ttl -o $1/output/output_test.nq
#test -f ./rmlmapper-6.5.1-r371-all.jar || curl -LO https://github.com/RMLio/rmlmapper-java/releases/download/v6.5.1/rmlmapper-6.5.1-r371-all.jar
#java -jar ./rmlmapper-6.5.1-r371-all.jar -m $1/output/mapping_without_views_old_rml.ttl -o $1/output/output_test.nq
java -jar ./rmlmapper.jar -m $1/output/mapping_without_views_old_rml.ttl -o $1/output/output_test.nq
sort -u $1/output.nq > $1/output/output_u.nq
sort -u $1/output/output_test.nq > $1/output/output_test_u.nq
diff --strip-trailing-cr $1/output/output_u.nq $1/output/output_test_u.nq > $1/output/diff.txt