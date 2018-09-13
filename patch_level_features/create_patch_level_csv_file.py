import sys
import os
import json 
import csv
import shutil
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python create_patch_level_csv_file.py";
    exit();    
    
  my_home="/home/bwang/patch_level";
  csv_folder = os.path.join(my_home, 'patch_level_csv_file2'); 
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
  patch_level_dataset = db2.patch_level_features;       
    
  feature_array=["case_id","image_width","image_height","mpp_x","mpp_y","patch_min_x_pixel","patch_min_y_pixel","patch_size","patch_polygon_area","patch_area_seleted_percentage","nucleus_area","percent_nuclear_material","tumorFlag","grayscale_patch_mean","grayscale_patch_std","Hematoxylin_patch_mean","Hematoxylin_patch_std","grayscale_segment_mean","grayscale_segment_std","Hematoxylin_segment_mean","Hematoxylin_segment_std","Flatness_segment_mean","Flatness_segment_std","Perimeter_segment_mean","Perimeter_segment_std","Circularity_segment_mean","Circularity_segment_std","r_GradientMean_segment_mean","r_GradientMean_segment_std","b_GradientMean_segment_mean","b_GradientMean_segment_std","r_cytoIntensityMean_segment_mean","r_cytoIntensityMean_segment_std","b_cytoIntensityMean_segment_mean","b_cytoIntensityMean_segment_std","Elongation_segment_mean","Elongation_segment_std","datetime"];   
  
  image_array=[];  
  for record in patch_level_dataset.distinct("case_id"):    
    image_array.append(record);
       
  for case_id in image_array: 
    ''' 
    csv_folder2 = os.path.join(csv_folder, case_id); 
    if not os.path.exists(csv_folder2):
      print '%s folder do not exist, then create it.' % csv_folder2;
      os.makedirs(csv_folder2);  
    '''      
    file_name="patch_level_feature_"+case_id+".csv";
    csv_dest_file = os.path.join(csv_folder, file_name);
    with open(csv_dest_file, 'wb') as csv_write: 
      csv_writer = csv.writer(csv_write);
      csv_writer.writerow(feature_array);           
      for record in patch_level_dataset.find({"case_id":case_id,"tumorFlag" : "tumor","$and":[{"percent_nuclear_material":{ "$ne": "n/a" }},{"percent_nuclear_material":{ "$gt": 0.0 }}]} ,{"_id":0}):
        row=[];
        for feature in feature_array:
          feature_value=record[feature];          
          row.append(feature_value);        
        csv_writer.writerow(row)    
          
  exit(); 
