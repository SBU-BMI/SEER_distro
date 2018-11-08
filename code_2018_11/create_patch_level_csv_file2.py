import sys
import os
import json 
import csv
import shutil
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python create_patch_level_csv_file2.py";
    exit();    
    
  my_home="/home/bwang/patch_level";
  csv_folder = os.path.join(my_home, 'patch_level_csv_file3'); 
  if not os.path.exists(csv_folder):
    print '%s folder do not exist, then create it.' % csv_folder;
    os.makedirs(csv_folder);
 
  
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
  patch_level_dataset = db2.patch_level_radiomics_features;       
    
  feature_array=["case_id","image_width","image_height","mpp_x","mpp_y","patch_x","patch_y","patch_width","patch_height","patch_area_micro","nuclei_area_micro","nuclei_ratio","nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","has_tumor","pseud_feat","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation","datetime"];   
  
  image_array=[];  
  for record in patch_level_dataset.distinct("case_id"):    
    image_array.append(record);
       
  for case_id in image_array: 
          
    file_name="patch_level_radiomics_feature_"+case_id+".csv";
    is_new_file=False;
    
    if os.path.isdir(csv_folder) and len(os.listdir(csv_folder)) > 0:                            
      csv_filename_list = [f for f in os.listdir(csv_folder) if f.endswith('.csv')] ;  
      if file_name not in csv_filename_list: 
        is_new_file=True;
    elif os.path.isdir(csv_folder) and len(os.listdir(csv_folder)) == 0:    
      is_new_file=True;
    
    if is_new_file:          
      csv_dest_file = os.path.join(csv_folder, file_name);
      with open(csv_dest_file, 'wb') as csv_write: 
        csv_writer = csv.writer(csv_write);
        csv_writer.writerow(feature_array);           
        for record in patch_level_dataset.find({"case_id":case_id} ,{"_id":0}):
          row=[];
          for feature in feature_array:
            feature_value=record[feature];          
            row.append(feature_value);        
          csv_writer.writerow(row)          
  exit(); 