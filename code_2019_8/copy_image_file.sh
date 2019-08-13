#!/bin/bash

input_file="image_file_path_2019_7_30"
IFS=$'\n' read -d '' -r -a caseid_list < $input_file

destdir="/data/shared/bwang/radiomics_feature/images" 
   

for file_path in "${caseid_list[@]}"
do 
  #echo $file_path
  case_id="$(cut -d'/' -f7 <<<"$file_path")"
  #echo $case_id  
  findit=0
  for j in `ls /data/shared/bwang/radiomics_feature/images | grep $case_id `;
  do 
    #echo $j;
    findit=1
  done
  
  if [[ $findit == 0 ]];then
   echo $file_path
   scp user@remote_url:$file_path  $destdir/. 
  fi     
done
