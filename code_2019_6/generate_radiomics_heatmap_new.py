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


############################################
def getImageWidthHeight(case_id):
  for record in patch_level_dataset.find({"case_id":case_id}).limit(1):
    image_w=record["image_width"]; 
    image_h=record["image_height"]; 
    return image_w,image_h;
##########################################

###################################################################### 
def save2Heatmap(case_id,feature):  
  case_id_short=case_id.replace("VTRPDAC_Test_", "") ;   
  specimen = "";
  study=""
  study_id = "quip" 
  execution_id = "patch_level_" + str(feature)+"_heatmap"; 
  #print case_id,feature,execution_id;  
  
  min_value=0.0;
  max_value=0.0; 
      
  if feature=="nuclei_ratio":
    min_value=0.0;
    max_value=1.0;
  else:  
    for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1,feature:{"$ne":"None"}},{feature:1,"_id":0}).sort(feature,-1).limit(1):    
      max_value = record[feature];       
      break;
    for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1,feature:{"$ne":"None"}},{feature:1,"_id":0}).sort(feature,1).limit(1):    
      min_value = record[feature];       
      break;  
  print case_id,feature,min_value,max_value;  
    
  dict_img = {}
  dict_img['case_id'] = case_id_short
  dict_img['subject_id'] = case_id_short
  dict_img['slide'] = case_id_short
  dict_img['specimen'] = specimen
  dict_img['study'] = study  
    
  dict_analysis = {}
  dict_analysis['study_id'] = study_id
  dict_analysis['computation'] = 'heatmap';
  dict_analysis['heatmap_type'] = 'pyradiomics_feature';
  
  image_width,image_height=getImageWidthHeight(case_id);
  #print case_id,patch_size,image_width,image_height;
  #return;  
  size_x=float(patch_size)/float(image_width);
  size_y=float(patch_size)/float(image_height); 
  dict_analysis['size'] = [size_x,size_y]
  dict_analysis['fields'] = [{"name":feature,"range":[min_value,max_value],"value":[min_value,max_value]}]    
  dict_analysis['execution_id'] = execution_id
  dict_analysis['source'] = 'computer'      
    
  dict_patch = collections.OrderedDict();    
  dict_provenance = {}
  dict_provenance['image'] = dict_img
  dict_provenance['analysis'] = dict_analysis   
  dict_patch['provenance'] = dict_provenance   
 
  data_array=[];  
  for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1,feature:{"$ne":"None"}}):    
    tmp_item=[];
    imageW=record["image_width"]; 
    imageH=record["image_height"];
    patch_x=record["patch_x"]; 
    patch_y=record["patch_y"]; 
    feature_value=record[feature]; 
    x1=float(patch_x)/float(imageW);
    y1=float(patch_y)/float(imageH);       
    tmp_item.append(x1);
    tmp_item.append(y1);
    tmp_item.append(feature_value);
    #print tmp_item;
    data_array.append(tmp_item); 
    #if x1>0.9:
    #  print  tmp_item;      
  #print data_array;
  dict_patch['data'] = data_array;          
  heatmap_dataset.insert_one(dict_patch);    
######################################################################
      
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_heatmap.py";
    exit(); 
   
  print " --- read config.json file ---" ;    
  config_json_file = "config_seer_pdac.json"; 
  with open(config_json_file) as json_data:
    d = json.load(json_data);        
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name = d['db_name'];    
    print patch_size,db_host,db_port,db_name;
  #exit();   
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name];  
  patch_level_dataset = db.patch_level_radiomics_features_copy; 
  heatmap_dataset = db.heatmap_tmp; 
  
  my_home="/home/bwang/patch_level";  
  code_base="/home/bwang/patch_level";   
  
  #global image_width,image_height;   
  #target_case_id="VTRPDAC_Test_PC3896_BL1_XX";                 
  
  feature_array=["nuclei_ratio","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"]  
  
  print '--- read image_list file ---- ';    
  image_list=[]; 
  target_image="VTRPDAC_Test_PC6725_BL1_00";  
  image_list.append(target_image); 
  
  '''
  image_list_file_name = "image_list_2019_6_6";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                      
      tmp=each_row[0];         
      image_list.append(tmp);           
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  '''
  #exit();
  
  #image_list=[];
  #image_list.append(target_case_id);
  
  '''
  for case_id in patch_level_dataset.distinct("case_id"):  
    #if case_id<>target_case_id:  
    image_list.append(case_id); 
  '''  
  #print "total rows from image_list file is %d " % len(image_list) ;  
  #exit();
  
  
  for case_id in image_list:
    '''
    for record in patch_level_dataset.find({"case_id":case_id}).limit(1):
      image_width=record["image_width"]; 
      image_height=record["image_height"];
      #patch_width=record["patch_width"]; 
      #patch_height=record["patch_height"];
      break;  
    print "--- case_id,image_width,image_height ---";  
    print case_id,image_width,image_height;  
    #continue;
    '''
    
    for index,feature in enumerate(feature_array[0:1]):
      #print index,feature;
      save2Heatmap(case_id,feature);     
  
  ''' 
  for case_id in image_list:
    if case_id==target_case_id:
      record_count=patch_level_dataset.find({"case_id":case_id}).count();
      print case_id,record_count;    
      save2Heatmap(case_id); 
    else:
      #continue;
      record_count=patch_level_dataset.find({"case_id":case_id}).count();
      print case_id,record_count;    
      save2Heatmap(case_id);         
  '''
  
  client.close();
  exit();   
    
  
