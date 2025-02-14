#! /bin/bash

function testing () {
  test -f ./burp.jar || curl -LO https://github.com/kg-construct/BURP/releases/download/v0.1.1/burp.jar
  cd $1
  echo $1
  python ../../view_to_csv.py --mapping mapping.ttl
  java -jar ../burp.jar -m ./mapping_without_views.ttl -o ./output_test.nq
  #java -jar ../rmlmapper.jar -m ./mapping_without_views.ttl -o ./output_test.nq
  result=`python ../compare.py output.nq output_test.nq`
  echo  "|" $dir "|" $result "|">> ../result.md
  rm view* mapping_without_views.ttl output_test.nq
  cd ..
}

for dir in ./*/ ;
do
  echo "testing $dir";
  testing $dir
done
