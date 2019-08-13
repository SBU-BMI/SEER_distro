from pymongo import MongoClient
import subprocess
import os
import sys
import csv
import json
import collections
import datetime
import numpy as np
import matplotlib.pyplot as plt; plt.rcdefaults()
from textwrap import wrap
import fnmatch
import operator
from contextlib import closing



#########################################
def saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array):
  dict_patch = collections.OrderedDict();
  dict_patch['case_id'] = case_id
  dict_patch['feature'] = feature
  dict_patch['data_range'] = data_range    
  dict_patch['hist_count_array'] = hist_count_array
  dict_patch['bin_edges_array'] = bin_edges_array    
  dict_patch['date'] = datetime.datetime.now();    
  patch_level_histogram.insert_one(dict_patch);   
#########################################
    

############################################
def findSegmentResultPath(root_path,target):  
  segmentResultPath=""; 
            
  for root, dirs, filelist in os.walk(root_path):
    for dir in dirs:
      #print dir;
      if operator.contains(dir, target):
        segmentResultPath =os.path.join(root, dir) ;
    else:
        # Continue if the inner loop wasn't broken.
        continue
    # Inner loop was broken, break the outer.
    break                 
        
  print (segmentResultPath);  
  return segmentResultPath;
###########################################
  

if __name__ == '__main__':    
  
  code_base=os.getcwd(); 
  #imageLocation        ="nfs003:/data/shared/bwang/radiomics_feature/images/"
  segmentResultLocation="nfs003:/data/shared/bwang/radiomics_feature/segment_results/"; 
  #outputLocation       ="nfs003:/data/shared/bwang/radiomics_feature/output"; 
  
  #setup  database
  patch_size =500;  
  db_host = "129.49.249.177";
  db_port = "27017";
  db_name = "quip";     
  print (patch_size,db_host,db_port,db_name);
    
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/',connect=False);     
  db = client[db_name];        
  radiomics_features_collection= db.patch_level_radiomics_features;
  
  existed_image_list=[];
  for case_id in radiomics_features_collection.distinct("case_id"):
    existed_image_list.append(case_id);     
  print ("total rows from existed_image_list file is %d " % len(existed_image_list)) ;  
  client.close();
  
  #setup image list calculated
  image_list=[];  
  image_list_file_name = "image_list_rutger_batch_3";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                      
      image_path=each_row[0];
      image_name=image_path.split('/')[6];
      case_id=image_name.rstrip('.tif');
      if not case_id in existed_image_list:         
        image_list.append(image_path);           
  print ("total rows from image_list file is %d " % len(image_list)) ; 
  
  
  #generate patch level radiomics feature dataset for all patches
  for image_path in image_list:
    image_name=image_path.split('/')[6];  
    case_id=image_name.rstrip(".tif");             
    segmentResultPath=segmentResultLocation + str(image_name);   
    cmd = "qsub -v case_id=" + case_id + ",imageFilePath="+ image_path +",segmentResultPath=" +segmentResultPath + " run_radiomics_rutger_all_patches_new.pbs";          
    print (cmd);
    proc = subprocess.Popen(cmd, shell=True); 
    status = proc.wait() ;               
  exit();       
