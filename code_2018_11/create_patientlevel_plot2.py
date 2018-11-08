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
    print "usage:python create_patientlevel_plot2.py";
    exit();    
  
  #my_home="/data1/bwang"  
  my_home="/home/bwang/patch_level";
  
  picture_folder = os.path.join(my_home, 'patient_level_plot'); 
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
  patient_level_dataset = db2.patient_level_radiomics_features_statistics;   
  
  feature_array=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"];
  
  for record in patient_level_dataset.find({},{"_id":0}):
    case_id=record["case_id"];
    picture_folder2 = os.path.join(picture_folder, case_id); 
    if not os.path.exists(picture_folder2):
      print '%s folder do not exist, then create it.' % picture_folder2;
      os.makedirs(picture_folder2);
    else:
      continue;#done it before,skip this record
    
    print "Process image " + str(case_id);  
    for feature in feature_array:
      try:
        feature_value=record[feature];
      except Exception as e:
        print e;
        continue;      
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
      plt.close('all');  
  exit(); 

