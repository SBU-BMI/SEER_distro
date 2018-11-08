import sys
import os
import json 
import csv
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python findDuplicateImage.py image_user_list_file";
    exit();    
    
  my_home="/home/bwang/patch_level";
 
  
  print " --- read config.json file ---" ;
  config_json_file_name = "config_cluster.json";  
  config_json_file = os.path.join(my_home, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;   
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db2 = client[db_name2];    
  patch_level_dataset = db2.patch_level_features;    
  
  print '--- read image_user_list file ---- ';  
  image_user_list_file = sys.argv[-1];
  index=0;
  image_list=[];  
  with open(image_user_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:             
      image_list.append(each_row[0]);                
  #print "total rows from image_user_list file is %d " % len(image_list) ; 
  #print image_list;
    
  image_array=[];  
  for record in patch_level_dataset.distinct("case_id"):    
    image_array.append(record); 
   
  findDuplicate=False;  
  for case_id in image_list:   
    if case_id in image_array :
      print case_id;
      findDuplicate=True;
  
  if findDuplicate:
    print "find some duplicated image case_id!"; 
  else:
    print "NOT find any duplicated image case_id!";
        
  exit(); 

