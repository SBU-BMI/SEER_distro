from pymongo import MongoClient
import subprocess
import os
import sys
import csv
import json

if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python run_all_steps.py";
    exit(); 
  
  #my_home="/data1/bwang";  
  code_base="/home/bwang/patch_level";
  
  print " --- read config.json file ---" ;
  config_json_file_name = "config_seahawk.json";  
  config_json_file = os.path.join(code_base, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;
    
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/',connect=False);     
  db = client[db_name1];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects; 
  
  '''
  #create image_list
  image_list=[];
  for case_id in images.distinct("case_id"):     
    image_id=str(case_id)+".tif"
    image_list.append(image_id);    
    print image_id;
  exit();
  '''
  
  print '--- read image_list file ---- ';    
  image_list=[];
  image_list_file_name = "image_list_2018_12_12";  
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                 
      image_list.append(each_row[0]);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  #print image_list;
  #exit();   
    
  step_num=1
  
  if step_num==1:      
    print '--- Step1 ---- '; 
    for image_id in image_list[100:]: 
      cmd = "qsub -v imageid=" + image_id + " run_radiomics_seahawk_all_patches.pbs";
      print cmd;
      proc = subprocess.Popen(cmd, shell=True) 
      status = proc.wait() ;
