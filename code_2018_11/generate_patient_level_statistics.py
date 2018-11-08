from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import affine_transform
from shapely import ops
from skimage import color
from skimage import io
from skimage.color import separate_stains,hed_from_rgb
from skimage import data
from pymongo import MongoClient
from bson import json_util 
from matplotlib.path import Path
from PIL import Image
import openslide
import numpy as np
import time
import pprint
import json 
import collections
import csv
import sys
import os
import shutil
import subprocess
import pipes
import shlex
import math
import datetime
import random

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_patient_level_statistics.py config.json";
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
  #exit();   
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name1];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;     
  
  db2 = client[db_name2];    
  images2 =db2.images; 
  metadata2=db2.metadata;
  objects2 = db2.objects;  
  
  patch_level_dataset = db2.patch_level_features;
  collection_saved    = db2.patient_level_statistics;  
  
  region_type="tumor";
  #region_type="non_tumor"; 
  
  image_list=[]; 
  image_list_existing=[];    
  for case_id in patch_level_dataset.distinct("case_id"):    
    image_list.append(case_id);
  
  for case_id in collection_saved.distinct("case_id"):    
    image_list_existing.append(case_id);
    
  print len(image_list), len(image_list_existing);
  #exit();
      
  feature_name_list=[];
  feature_name_list.append("percent_nuclear_material");
  feature_name_list.append("grayscale_patch_mean");
  feature_name_list.append("grayscale_patch_std");
  feature_name_list.append("Hematoxylin_patch_mean");
  feature_name_list.append("Hematoxylin_patch_std");
  feature_name_list.append("Flatness_segment_mean");
  feature_name_list.append("Flatness_segment_std");
  feature_name_list.append("Perimeter_segment_mean");
  feature_name_list.append("Perimeter_segment_std");
  feature_name_list.append("Circularity_segment_mean");
  feature_name_list.append("Circularity_segment_std");
  feature_name_list.append("r_GradientMean_segment_mean");
  feature_name_list.append("r_GradientMean_segment_std");
  feature_name_list.append("b_GradientMean_segment_mean");
  feature_name_list.append("b_GradientMean_segment_std");
  feature_name_list.append("r_cytoIntensityMean_segment_mean");
  feature_name_list.append("r_cytoIntensityMean_segment_std");
  feature_name_list.append("b_cytoIntensityMean_segment_mean");
  feature_name_list.append("b_cytoIntensityMean_segment_std");
  feature_name_list.append("Elongation_segment_mean");
  feature_name_list.append("Elongation_segment_std");  
  
  
  print '--- process image_list  ---- '; 
  image_count=0;
  for case_id in image_list:  
    if case_id in image_list_existing:
      print str(case_id) + " existed! skip it.";
      continue;
    print   case_id;
        
    percent_nuclear_material_array=[];
    grayscale_patch_mean_array=[];
    grayscale_patch_std_array=[];
    Hematoxylin_patch_mean_array=[];
    Hematoxylin_patch_std_array=[];     
    Flatness_segment_mean_array=[]; 
    Flatness_segment_std_array=[];
    Perimeter_segment_mean_array=[];
    Perimeter_segment_std_array=[];
    Circularity_segment_mean_array=[];
    Circularity_segment_std_array=[];
    r_GradientMean_segment_mean_array=[];
    r_GradientMean_segment_std_array=[];
    b_GradientMean_segment_mean_array=[];
    b_GradientMean_segment_std_array=[];
    r_cytoIntensityMean_segment_mean_array=[];
    r_cytoIntensityMean_segment_std_array=[];
    b_cytoIntensityMean_segment_mean_array=[];
    b_cytoIntensityMean_segment_std_array=[];    
    Elongation_segment_mean_array=[];
    Elongation_segment_std_array=[];
    
    for feature_record in patch_level_dataset.find({"case_id":case_id,                                                    
                                                    "tumorFlag":region_type,
                                                    "percent_nuclear_material":{ "$gte": 2.0 } }):                                                      
      for feature_name in feature_name_list:        
        feature_value= feature_record[feature_name];        
        if (feature_name=="percent_nuclear_material"):    
          percent_nuclear_material_array.append(feature_value);        
        elif (feature_name=="grayscale_patch_mean"):    
          grayscale_patch_mean_array.append(feature_value);
        elif (feature_name=="grayscale_patch_std"):    
          grayscale_patch_std_array.append(feature_value); 
        elif (feature_name=="Hematoxylin_patch_mean"):    
          Hematoxylin_patch_mean_array.append(feature_value);
        elif (feature_name=="Hematoxylin_patch_std"):    
          Hematoxylin_patch_std_array.append(feature_value);        
        elif (feature_name=="Flatness_segment_mean"):    
          Flatness_segment_mean_array.append(feature_value);
        elif (feature_name=="Flatness_segment_std"):    
          Flatness_segment_std_array.append(feature_value); 
        elif (feature_name=="Perimeter_segment_mean"):    
          Perimeter_segment_mean_array.append(feature_value);
        elif (feature_name=="Perimeter_segment_std"):    
          Perimeter_segment_std_array.append(feature_value);        
        elif (feature_name=="Circularity_segment_mean"):    
          Circularity_segment_mean_array.append(feature_value);
        elif (feature_name=="Circularity_segment_std"):    
          Circularity_segment_std_array.append(feature_value); 
        elif (feature_name=="r_GradientMean_segment_mean"):    
          r_GradientMean_segment_mean_array.append(feature_value);
        elif (feature_name=="r_GradientMean_segment_std"):    
          r_GradientMean_segment_std_array.append(feature_value);        
        elif (feature_name=="b_GradientMean_segment_mean"):    
          b_GradientMean_segment_mean_array.append(feature_value);
        elif (feature_name=="b_GradientMean_segment_std"):    
          b_GradientMean_segment_std_array.append(feature_value); 
        elif (feature_name=="r_cytoIntensityMean_segment_mean"):    
          r_cytoIntensityMean_segment_mean_array.append(feature_value);  
        elif (feature_name=="r_cytoIntensityMean_segment_std"):    
          r_cytoIntensityMean_segment_std_array.append(feature_value);
        elif (feature_name=="b_cytoIntensityMean_segment_mean"):    
          b_cytoIntensityMean_segment_mean_array.append(feature_value); 
        elif (feature_name=="b_cytoIntensityMean_segment_std"):    
          b_cytoIntensityMean_segment_std_array.append(feature_value);      
        elif (feature_name=="Elongation_segment_mean"):    
          Elongation_segment_mean_array.append(feature_value); 
        elif (feature_name=="Elongation_segment_std"):    
          Elongation_segment_std_array.append(feature_value); 
      
    dict_data = collections.OrderedDict(); 
    dict_data['case_id']=case_id;
    dict_data['datetime'] = datetime.datetime.now();
    
    feature_data_available=False;
    for feature_name in feature_name_list:
      if (feature_name=="percent_nuclear_material"):    
        feature_array=percent_nuclear_material_array;        
      elif (feature_name=="grayscale_patch_mean"):    
        feature_array=grayscale_patch_mean_array;
      elif (feature_name=="grayscale_patch_std"):    
        feature_array=grayscale_patch_std_array; 
      elif (feature_name=="Hematoxylin_patch_mean"):    
        feature_array=Hematoxylin_patch_mean_array;
      elif (feature_name=="Hematoxylin_patch_std"):    
        feature_array=Hematoxylin_patch_std_array;        
      elif (feature_name=="Flatness_segment_mean"):    
        feature_array=Flatness_segment_mean_array;
      elif (feature_name=="Flatness_segment_std"):    
        feature_array=Flatness_segment_std_array; 
      elif (feature_name=="Perimeter_segment_mean"):    
        feature_array=Perimeter_segment_mean_array;
      elif (feature_name=="Perimeter_segment_std"):    
        feature_array=Perimeter_segment_std_array;        
      elif (feature_name=="Circularity_segment_mean"):    
        feature_array=Circularity_segment_mean_array;
      elif (feature_name=="Circularity_segment_std"):    
        feature_array=Circularity_segment_std_array; 
      elif (feature_name=="r_GradientMean_segment_mean"):    
        feature_array=r_GradientMean_segment_mean_array;
      elif (feature_name=="r_GradientMean_segment_std"):    
        feature_array=r_GradientMean_segment_std_array;        
      elif (feature_name=="b_GradientMean_segment_mean"):    
        feature_array=b_GradientMean_segment_mean_array;
      elif (feature_name=="b_GradientMean_segment_std"):    
        feature_array=b_GradientMean_segment_std_array; 
      elif (feature_name=="r_cytoIntensityMean_segment_mean"):    
        feature_array=r_cytoIntensityMean_segment_mean_array;  
      elif (feature_name=="r_cytoIntensityMean_segment_std"):    
        feature_array=r_cytoIntensityMean_segment_std_array;
      elif (feature_name=="b_cytoIntensityMean_segment_mean"):    
        feature_array=b_cytoIntensityMean_segment_mean_array; 
      elif (feature_name=="b_cytoIntensityMean_segment_std"):    
        feature_array=b_cytoIntensityMean_segment_std_array;
      elif (feature_name=="Elongation_segment_mean"):    
        feature_array=Elongation_segment_mean_array; 
      elif (feature_name=="Elongation_segment_std"):    
        feature_array=Elongation_segment_std_array;
      
      if  len(feature_array) <1: 
        continue;
      else:
        feature_data_available=True;
            
      dict_feature = {}      
      dict_feature['10th'] = np.percentile(feature_array,10);
      dict_feature['25th'] = np.percentile(feature_array,25);
      dict_feature['50th'] = np.percentile(feature_array,50); 
      dict_feature['75th'] = np.percentile(feature_array,75);
      dict_feature['90th'] = np.percentile(feature_array,90);   
      dict_data[feature_name] = dict_feature;    
    
    if feature_data_available:         
      collection_saved.insert_one(dict_data); 
      image_count+=1;
      
  print "total images is  %d" % image_count       
  exit(); 
  
  
  
  
  