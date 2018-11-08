from pymongo import MongoClient
import numpy as np
import json 
import collections
import csv
import sys
import os
import shutil
import subprocess
import math
import datetime
import random

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python create_patient_level_statistics.py config.json";
    exit(); 
   
  print " --- read config.json file ---" ;
  config_json_file = sys.argv[-1];  
  with open(config_json_file) as json_data:
    d = json.load(json_data);       
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print db_host,db_port,db_name1,db_name2;     
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name1];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;     
  
  db2 = client[db_name2];    
  images2 =db2.images; 
  metadata2=db2.metadata;
  objects2 = db2.objects;  
  
  patch_level_dataset = db2.patch_level_radiomics_features;
  collection_saved    = db2.patient_level_radiomics_features_statistics;   
  
  has_tumor=1 #tumor region    
  
  image_list=[]; 
  image_list_existing=[];    
  for case_id in patch_level_dataset.distinct("case_id"):    
    image_list.append(case_id);
  
  for case_id in collection_saved.distinct("case_id"):    
    image_list_existing.append(case_id);
    
  print len(image_list), len(image_list_existing);  
  
  feature_array=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"]; 
  
  print '--- process image_list  ---- '; 
  image_count=0;
  for case_id in image_list:  
    if case_id in image_list_existing:
      print str(case_id) + " existed! skip it.";
      continue;
    print case_id;  
    
    dict_data = collections.OrderedDict(); 
    dict_data['case_id']=case_id;
    dict_data['datetime'] = datetime.datetime.now();
    
    feature_data_available=False;
    for index,feature in enumerate(feature_array):         
      feature_value_array=[];        
      for record in patch_level_dataset.find({"case_id":case_id,"has_tumor":1,"$and":[{feature:{ "$ne": "None" }},{feature:{ "$gte": 0.0 }}]} ,{feature:1,"_id":0}):        
          feature_value=record[feature];
          feature_value_array.append(feature_value); 
     
      if  len(feature_value_array) <1: 
        continue;
      else:
        feature_data_available=True;
            
      dict_feature = {}      
      dict_feature['10th'] = np.percentile(feature_value_array,10);
      dict_feature['25th'] = np.percentile(feature_value_array,25);
      dict_feature['50th'] = np.percentile(feature_value_array,50); 
      dict_feature['75th'] = np.percentile(feature_value_array,75);
      dict_feature['90th'] = np.percentile(feature_value_array,90);   
      dict_data[feature] = dict_feature;    
    
    if feature_data_available:         
      collection_saved.insert_one(dict_data); 
      image_count+=1;
      
  print "total images is  %d" % image_count       
  exit(); 
   