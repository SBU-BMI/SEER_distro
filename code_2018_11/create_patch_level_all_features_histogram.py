import matplotlib.pyplot as plt
plt.switch_backend('agg')
from textwrap import wrap
import numpy as np
import collections
import sys
import os
import json 
import csv
import datetime
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python create_patch_level_all_features_histogram.py";
    exit();    
  
  #my_home="/data1/bwang"  
  my_home="/home/bwang/patch_level";
  
  picture_folder = os.path.join(my_home, 'patch_level_all_features_plot'); 
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
  
  print '--- read all_features_list.txt file ---- ';
  all_feature_file="all_features_list.txt";  
  index=0;
  feature_list=[];  
  with open(all_feature_file, 'r') as my_file:
    reader = csv.reader(my_file)
    my_list = list(reader);
    for each_row in my_list:       
      #print each_row; 
      tmp_feature= each_row[0];               
      feature_list.append(tmp_feature);                
  print "total rows from all_features_list file is %d " % len(feature_list) ; 
  #print feature_list;
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
  
  patch_level_dataset   = db2.patch_level_all_features;  
  patch_level_histogram = db2.all_features_histogram;
  
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
  
  image_array=[];  
  for record in patch_level_dataset.distinct("case_id"):    
    image_array.append(record);    

  data_range="patch_level";
  for case_id in image_array[2:]:
    picture_folder2 = os.path.join(picture_folder, case_id); 
    if not os.path.exists(picture_folder2):
      print '%s folder do not exist, then create it.' % picture_folder2;
      os.makedirs(picture_folder2);
    else:
      continue;#done it before,skip this record    
        
    for index,feature in enumerate(feature_list):  
      #create histogram of feature mean value       
      feature_value_array=[];   
      hist_count_array=[];
      bin_edges_array=[];
      feature_mean=str(feature)+"_mean";          
      for record in patch_level_dataset.find({"case_id":case_id,"tumorFlag" : "tumor","$and":[{feature_mean:{ "$ne": "n/a" }},{feature_mean:{ "$gte": 0.0 }}]} ,{feature_mean:1,"_id":0}):
        feature_value=record[feature_mean];
        feature_value_array.append(feature_value); 
      print case_id,feature_mean;   
      #print feature_value_array; 
      total_patch_count=len(feature_value_array); 
      #print total_patch_count;      
      if len(feature_value_array) >0: 
        fig, ax = plt.subplots();    
        n, bins, patches = plt.hist(feature_value_array, bins=15,facecolor='blue');   
        #print n, bins;  
        plt.xlabel(feature_mean)
        plt.ylabel('Patch Count')
        plt.title("\n".join(wrap("patch level "+ feature_mean+ ' Histogram of image '+ str(case_id))))
        #Tweak spacing to prevent clipping of ylabel
        plt.subplots_adjust(left=0.15)
        plt.grid(True);           
        # place a text box in upper left in axes coords
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textstr="Total patch count: " + str(total_patch_count);
        ax.text(0.6, 0.95, textstr, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props);      
        #plt.show();
        #break;        
        file_name="patch_level_histogram_"+case_id+"_"+feature_mean+".png";  
        graphic_file_path = os.path.join(picture_folder2, file_name);
        plt.savefig(graphic_file_path); 
        plt.gcf().clear(); 
        #plt.close(fig)
        plt.close('all')
        #save result to database
        for count in n:        
          hist_count_array.append(int(count));
        for bin_edge in bins:        
          bin_edges_array.append(float(bin_edge));   
        saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array);  
      
      #create histogram of feature std value
      feature_value_array=[];   
      hist_count_array=[];
      bin_edges_array=[];
      feature_std=str(feature)+"_std"  
      for record in patch_level_dataset.find({"case_id":case_id,"tumorFlag" : "tumor","$and":[{feature_std:{ "$ne": "n/a" }},{feature_std:{ "$gte": 0.0 }}]} ,{feature_std:1,"_id":0}):
        feature_value=record[feature_std];
        feature_value_array.append(feature_value); 
      print case_id,feature_std;   
      #print feature_value_array; 
      total_patch_count=len(feature_value_array); 
      #print total_patch_count;      
      if len(feature_value_array) >0: 
        fig, ax = plt.subplots();    
        n, bins, patches = plt.hist(feature_value_array, bins=15,facecolor='blue');   
        #print n, bins;  
        plt.xlabel(feature_std)
        plt.ylabel('Patch Count')
        plt.title("\n".join(wrap("patch level "+ feature_std+ ' Histogram of image '+ str(case_id))))
        #Tweak spacing to prevent clipping of ylabel
        plt.subplots_adjust(left=0.15)
        plt.grid(True);           
        # place a text box in upper left in axes coords
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        textstr="Total patch count: " + str(total_patch_count);
        ax.text(0.6, 0.95, textstr, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props);      
        #plt.show();
        file_name="patch_level_histogram_"+case_id+"_"+feature_std+".png";  
        graphic_file_path = os.path.join(picture_folder2, file_name);
        plt.savefig(graphic_file_path); 
        plt.gcf().clear();
        #plt.close(fig) 
        plt.close('all')
        #save result to database
        for count in n:        
          hist_count_array.append(int(count));
        for bin_edge in bins:        
          bin_edges_array.append(float(bin_edge));   
        saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array);                  
  exit(); 

