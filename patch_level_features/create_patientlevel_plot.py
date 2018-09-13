import matplotlib.pyplot as plt; plt.rcdefaults()
from textwrap import wrap
import numpy as np
import collections
import sys
import os
import json 
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python create_patch_level_histogram.py";
    exit();    
  
  #my_home="/data1/bwang"  
  my_home="/home/bwang/patch_level";
  
  picture_folder = os.path.join(my_home, 'patient_level_plot2'); 
  if not os.path.exists(picture_folder):
    print '%s folder do not exist, then create it.' % picture_folder;
    os.makedirs(picture_folder);
  
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
    print "---------------------------------------------"  
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db2 = client[db_name2];    
  patient_level_dataset = db2.patient_level_statistics; 
  
  
  feature_array=["percent_nuclear_material","grayscale_patch_mean","grayscale_patch_std","Hematoxylin_patch_mean","Hematoxylin_patch_std","Flatness_segment_mean","Flatness_segment_std","Perimeter_segment_mean","Perimeter_segment_std","Circularity_segment_mean","Circularity_segment_std","r_GradientMean_segment_mean","r_GradientMean_segment_std","b_GradientMean_segment_mean","b_GradientMean_segment_std","r_cytoIntensityMean_segment_mean","r_cytoIntensityMean_segment_std","b_cytoIntensityMean_segment_mean","b_cytoIntensityMean_segment_std","Elongation_segment_mean","Elongation_segment_std"]
  
  for record in patient_level_dataset.find({},{"_id":0}):
    case_id=record["case_id"];
    picture_folder2 = os.path.join(picture_folder, case_id); 
    if not os.path.exists(picture_folder2):
      print '%s folder do not exist, then create it.' % picture_folder2;
      os.makedirs(picture_folder2);
    
    for feature in feature_array:
      feature_value=record[feature];
      percentile_10th = feature_value["10th"];
      percentile_25th = feature_value["25th"];
      percentile_50th = feature_value["50th"];
      percentile_75th = feature_value["75th"];
      percentile_90th = feature_value["90th"];
      objects = ('10th', '25th', '50th', '75th', '90th')
      y_pos = np.arange(len(objects))
      percentile = [percentile_10th,percentile_25th,percentile_50th,percentile_75th,percentile_90th]; 
      plt.bar(y_pos, percentile, align='center', alpha=0.5)
      plt.xticks(y_pos, objects)
      plt.ylabel(feature)       
      plt.title("\n".join(wrap("patient level "+ feature+ ' percentile of image '+ str(case_id))))
      plt.subplots_adjust(left=0.15)
      plt.grid(True);
      #plt.show()
      file_name="patient_level_percentile_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder2, file_name);
      plt.savefig(graphic_file_path); 
      plt.gcf().clear();    
  exit(); 
