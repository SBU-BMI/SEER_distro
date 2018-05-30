#!/bin/bash

input_file="case_id_list_2017_12_12"
IFS=$'\n' read -d '' -r -a caseid_list < $input_file

for case_id in "${caseid_list[@]}"
do  
  qsub -v caseid=$case_id run_jobs.pbs   
done
