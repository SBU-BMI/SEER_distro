from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import affine_transform
from shapely.validation import explain_validity 
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
from datetime import datetime
import random
import concurrent.futures 
import logging
    
    
if __name__ == '__main__':
  if len(sys.argv)<2:
    print "usage:python run_patch_level_all_features.py case_id user";
    exit(); 
    
  LOG_FILENAME = 'readme.log'  
  logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG) 
   
  csv.field_size_limit(sys.maxsize); 
  max_workers=16;  
  
  case_id = sys.argv[1]; 
  user= sys.argv[2] ;
  
  image_list=[];  
  tmp_array=[[],[]];
  tmp_array[0]=case_id;   
  tmp_array[1]=user;
  image_list.append(tmp_array);   
  print image_list;  
  
  my_home="/data1/bwang"  
  #my_home="/home/bwang/patch_level"
  
  remote_dataset_folder="nfs004:/data/shared/bwang/composite_dataset";   
  local_dataset_folder = os.path.join(my_home, 'dataset');  
  if not os.path.exists(local_dataset_folder):
    print '%s folder do not exist, then create it.' % local_dataset_folder;
    os.makedirs(local_dataset_folder); 
  
  remote_image_folder="nfs001:/data/shared/tcga_analysis/seer_data/images";      
  local_image_folder = os.path.join(my_home, 'img'); 
  if not os.path.exists(local_image_folder):
    print '%s folder do not exist, then create it.' % local_image_folder;
    os.makedirs(local_image_folder);
  
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
      feature_list.append(each_row[0]);                
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
    
  collection_saved= db2.patch_level_all_features; 
  segment_count_collection=db2.segment_count_by_image;
  
  image_width=0;
  image_height=0; 
  mpp_x=0.0;
  mpp_y=0.0;   
  
  #######################################
  def findPrefixList(case_id):    
    prefix_list=[];  
    input_file="case_id_prefix.txt"
    prefix_file = os.path.join(my_home, input_file); 
    with open(prefix_file, 'r') as my_file:
      reader = csv.reader(my_file,delimiter=',')
      my_list = list(reader);
      for each_row in my_list:      
        file_path=each_row[0];#path        
        if file_path.find(case_id) <> -1:#find it!
          perfix_path = each_row[0];           
          position_1=perfix_path.rfind('/')+1;
          position_2=len(perfix_path);
          prefix=perfix_path[position_1:position_2];         
          prefix_list.append(prefix)           
    return  prefix_list;  
  ###############################################
  
  
  ###############################################
  def read_csv_data_file(file_path,data_file):    
    obj_list=[];
    csv_file = os.path.join(file_path, data_file);
    #dict_featuer_index = {}  
    feature_index_list=[];      
    with open(csv_file, 'rb') as csv_read:
      reader = csv.reader(csv_read);
      headers = reader.next();          
      polygon_index= headers.index('Polygon');        
      for feature in feature_list:          
        feature_index=headers.index(feature);        
        tmp=[[],[]]
        tmp[0]=feature;
        tmp[1]=feature_index;
        feature_index_list.append(tmp);                              
      for row in reader: 
        feature_value_list=[];
        patch_item=[[],[],[]];           
        current_polygon=row[polygon_index] ;        
        new_polygon=[];            
        tmp_str=str(current_polygon);            
        tmp_str=tmp_str.replace('[','');
        tmp_str=tmp_str.replace(']','');
        split_str=tmp_str.split(':');
        for i in range(0, len(split_str)-1, 2):
          point=[float(split_str[i])/float(image_width),float(split_str[i+1])/float(image_height)];
          new_polygon.append(point);              
        tmp_poly=[tuple(i) for i in new_polygon];
        computer_polygon0 = Polygon(tmp_poly);
        computer_polygon = computer_polygon0.buffer(0);         
        patch_item[0]=computer_polygon;
        patch_item[1]=computer_polygon0;
        for item in feature_index_list:
          feature=item[0];
          feature_index=item[1];
          feature_value=row[feature_index]
          tmp=[[],[]]
          tmp[0]=feature;
          tmp[1]=feature_value;
          feature_value_list.append(tmp);
        patch_item[2]=feature_value_list;              
        obj_list.append(patch_item);    
    return  obj_list;             
  ###############################################
  
  ###############################################
  def getImageMetaData(local_img_folder,prefix_list):
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
         json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;                       
         for json_filename in json_filename_list:             
           with open(os.path.join(detail_local_folder, json_filename)) as f:
             data = json.load(f);             
             image_width=data["image_width"];
             image_height=data["image_height"];            
             return image_width,image_height;  
  ###############################################  
  
  ###############################################
  def getTileMetaData(tile_min_point,local_img_folder,prefix_list):
    x=tile_min_point[0];
    y=tile_min_point[1];
    tmp_string="_x"+str(x)+"_y" + str(y);      
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
         json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;                       
         for json_filename in json_filename_list:   
           if (json_filename.find(tmp_string) <> -1):  #find it!        
             with open(os.path.join(detail_local_folder, json_filename)) as f:
               data = json.load(f);                  
               tile_width=data["tile_width"];
               tile_height=data["tile_height"];                      
               return tile_width,tile_height;  
  ############################################### 
   
  #######################################################
  def findUniqueTileList(local_img_folder,prefix_list):
    tile_min_point_list=[] 
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
         json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;                      
         for json_filename in json_filename_list:                        
           with open(os.path.join(detail_local_folder, json_filename)) as f:
             data = json.load(f);            
             tile_minx=data["tile_minx"];
             tile_miny=data["tile_miny"];                         
             point=[tile_minx,tile_miny];
             tile_min_point_list.append(point);     
    tmp_set = set(map(tuple,tile_min_point_list))
    unique_tile_min_point_list = map(list,tmp_set)
    return unique_tile_min_point_list;
  #######################################################    
  
  ###############################################
  def getCompositeDatasetExecutionID(case_id):
    execution_id="";
    for record in metadata2.find({"image.case_id":case_id,                 
				                          "provenance.analysis_execution_id":{'$regex' : 'composite_dataset', '$options' : 'i'}}).limit(1): 
      execution_id=record["provenance"]["analysis_execution_id"];
      break;
    return execution_id;    
  #################################################     
  
  #############################################
  def findTumor_NonTumorRegions(case_id,user):
    execution_id=user+"_Tumor_Region";
    execution_id2=user+"_Non_Tumor_Region";
    
    #handle only tumor region overlap
    humanMarkupList_tumor=[];
    tmp_tumor_markup_list=[];
    
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id},
                                 {"geometry":1,"_id":1}):                         
      tmp_tumor_markup_list.append(humarkup);    
              
    index_intersected=[];                                
    for index1 in range(0, len(tmp_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      tmp_tumor_markup1=tmp_tumor_markup_list[index1];                               
      humarkup_polygon_tmp1=tmp_tumor_markup1["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i1) for i1 in humarkup_polygon_tmp1];
      tmp_polygon1 = Polygon(tmp_polygon);    
      humarkup_polygon1 = tmp_polygon1.buffer(0);      
      humarkup_polygon_bound1= humarkup_polygon1.bounds;      
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_tumor_markup_list)):  
        tmp_tumor_markup2=tmp_tumor_markup_list[index2];                               
        humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
        tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
        tmp_polygon22 = Polygon(tmp_polygon2);        
        humarkup_polygon2 = tmp_polygon22.buffer(0); 
        if (index1 <> index2):
          if (humarkup_polygon1.within(humarkup_polygon2)):    
            is_within=True;            
            break;              
          if (humarkup_polygon1.intersects(humarkup_polygon2)):
            humarkup_polygon1=humarkup_polygon1.union(humarkup_polygon2); 
            is_intersect=True;
            index_intersected.append(index2);                
      if(not is_within and not is_intersect):
        humanMarkupList_tumor.append(humarkup_polygon1);          
      if(is_within):
        continue;         
      if(is_intersect):          
        humanMarkupList_tumor.append(humarkup_polygon1);            
        
    #handle only non tumor region overlap
    humanMarkupList_non_tumor=[];
    tmp_non_tumor_markup_list=[];
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id2},
                                 {"geometry":1,"_id":0}):
      tmp_non_tumor_markup_list.append(humarkup);     
        
    index_intersected=[];                                
    for index1 in range(0, len(tmp_non_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      tmp_tumor_markup1=tmp_non_tumor_markup_list[index1];                               
      humarkup_polygon_tmp1=tmp_tumor_markup1["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i1) for i1 in humarkup_polygon_tmp1];
      tmp_polygon1 = Polygon(tmp_polygon);      
      humarkup_polygon1 = tmp_polygon1.convex_hull;
      humarkup_polygon1 = humarkup_polygon1.buffer(0);
      humarkup_polygon_bound1= humarkup_polygon1.bounds;
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_non_tumor_markup_list)):  
        tmp_tumor_markup2=tmp_non_tumor_markup_list[index2];                               
        humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
        tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
        tmp_polygon22 = Polygon(tmp_polygon2);
        humarkup_polygon2=tmp_polygon22.convex_hull;
        humarkup_polygon2 = humarkup_polygon2.buffer(0);
        if (index1 <> index2):
          if (humarkup_polygon1.within(humarkup_polygon2)):    
            is_within=True;            
            break;              
          if (humarkup_polygon1.intersects(humarkup_polygon2)):
            humarkup_polygon1=humarkup_polygon1.union(humarkup_polygon2); 
            is_intersect=True;
            index_intersected.append(index2);                
      if(not is_within and not is_intersect):
        humanMarkupList_non_tumor.append(humarkup_polygon1);          
      if(is_within):
        continue;         
      if(is_intersect):          
        humanMarkupList_non_tumor.append(humarkup_polygon1);
        
    #handle tumor and non tumor region cross overlap
    for index1,tumor_region in enumerate(humanMarkupList_tumor):
      for index2,non_tumor_region in enumerate(humanMarkupList_non_tumor):
        if (tumor_region.within(non_tumor_region)): 
          ext_polygon_intersect_points =list(zip(*non_tumor_region.exterior.coords.xy));   
          int_polygon_intersect_points =list(zip(*tumor_region.exterior.coords.xy)); 
          newPoly = Polygon(ext_polygon_intersect_points,[int_polygon_intersect_points]);
          humanMarkupList_non_tumor[index2]=newPoly;#add a hole to this polygon
        elif (non_tumor_region.within(tumor_region)): 
          ext_polygon_intersect_points =list(zip(*tumor_region.exterior.coords.xy));   
          int_polygon_intersect_points =list(zip(*non_tumor_region.exterior.coords.xy)); 
          newPoly = Polygon(ext_polygon_intersect_points,[int_polygon_intersect_points]);
          humanMarkupList_tumor[index1]=newPoly;#add a hole to this polygon   
    
    return  humanMarkupList_tumor,humanMarkupList_non_tumor;     
  ################################################
  
  #######################################
  def findImagePath(case_id):
    image_path="";  
    input_file="image_path.txt"
    image_path_file = os.path.join(my_home, input_file); 
    with open(image_path_file, 'r') as my_file:
      reader = csv.reader(my_file,delimiter=',')
      my_list = list(reader);
      for each_row in my_list:      
        file_path=each_row[0];#path
        if file_path.find(case_id) <> -1:#find it!
          image_path = each_row[0]; 
          image_path = image_path.replace('./','');       
          break
    return  image_path;  
  ###############################################  
   
  
  ##################################################
  def removeOverlapPolygon(nuclear_item_list):
    overlapPolygonIndx=999999;
    overlapPolygonIndxList=[];
    nuclear_item_list_new=[];
    nuclues_polygon_count=len(nuclear_item_list);
    for i2 in range(0,nuclues_polygon_count-1):
      for j2 in range(1,nuclues_polygon_count): 
        if (i2<>j2):
          polygon1=nuclear_item_list[i2][0];
          polygon2=nuclear_item_list[j2][0];
          if (polygon1.within(polygon2)):
            print "polygon " + str(i2)+" is within polygon " + str(j2);
            overlapPolygonIndx=j2;
            overlapPolygonIndxList.append(overlapPolygonIndx);
            #del nuclear_item_list[overlapPolygonIndx];
            #return nuclear_item_list;
          if (polygon2.within(polygon1)):
            print "polygon " + str(j2)+" is within polygon " + str(i2);
            overlapPolygonIndx=i2;
            overlapPolygonIndxList.append(overlapPolygonIndx);
            #del nuclear_item_list[overlapPolygonIndx];
            #return nuclear_item_list;  
                                         
    for index,item in enumerate(nuclear_item_list):
      if index not in overlapPolygonIndxList : 
        nuclear_item_list_new.append(item); 
    #print len(nuclear_item_list),len(nuclear_item_list_new);  
           
    return nuclear_item_list_new;     
  ##################################################
  
  #########################################################
  def saveFeatures2MongoDB(case_id,image_width,image_height,mpp_x,mpp_y,user,tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,tumorFlag,feature_result,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count):
    patch_feature_data = collections.OrderedDict();
    patch_feature_data['case_id'] = case_id;
    patch_feature_data['image_width'] = image_width;
    patch_feature_data['image_height'] = image_height;  
    patch_feature_data['mpp_x'] = mpp_x;
    patch_feature_data['mpp_y'] = mpp_y;      
    patch_feature_data['user'] = user;
    patch_feature_data['tile_index'] = tile_index;    
    patch_feature_data['patch_min_x_pixel'] =patch_min_x_pixel;
    patch_feature_data['patch_min_y_pixel'] = patch_min_y_pixel;    
    patch_feature_data['patch_size'] = patch_size;     
    patch_feature_data['tumorFlag'] = tumorFlag;  
    for item  in feature_result:
      feature=item[0]
      mean_value=item[1]
      std_value=item[2]
      feature_mean=str(feature)+"_mean";
      feature_std=str(feature)+"_std";
      patch_feature_data[feature_mean] = mean_value;
      patch_feature_data[feature_std] = std_value;
    
    patch_feature_data['total_nuclues_polygon_count'] =total_nuclues_polygon_count;
    patch_feature_data['invalid_nuclues_polygon_count'] = invalid_nuclues_polygon_count;    
    patch_feature_data['overlap_nuclues_polygon_count'] = overlap_nuclues_polygon_count;          
    patch_feature_data['datetime'] = datetime.now();               
    collection_saved.insert_one(patch_feature_data);         
  ######################################################################  
  
  #########################################################
  def saveSegmentCount2MongoDB(case_id,final_total_nuclues_polygon_count,final_invalid_nuclues_polygon_count,final_overlap_nuclues_polygon_count):
    patch_feature_data = collections.OrderedDict();
    patch_feature_data['case_id'] = case_id;    
    patch_feature_data['final_total_nuclues_polygon_count'] = final_total_nuclues_polygon_count;
    patch_feature_data['final_invalid_nuclues_polygon_count'] = final_invalid_nuclues_polygon_count;  
    patch_feature_data['final_overlap_nuclues_polygon_count'] = final_overlap_nuclues_polygon_count;             
    patch_feature_data['datetime'] = datetime.now();               
    segment_count_collection.insert_one(patch_feature_data);         
  ###################################################################### 
  
  ######################################################################
  def process_one_patch(case_id,user,tile_index,tumorFlag,image_width,image_height,mpp_x,mpp_y,patch_polygon_original,nuclues_item_list,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count):    
    patch_min_x_pixel =int(patch_polygon_original[0][0]*image_width);
    patch_min_y_pixel =int(patch_polygon_original[0][1]*image_height); 
       
    print " ---- tile_index,patch_min_x_pixel,patch_min_y_pixel,len(nuclues_item_list) ---";
    print tile_index,patch_min_x_pixel,patch_min_y_pixel,len(nuclues_item_list);  
        
    cols_count=len(feature_list);  
    rows_count=len(nuclues_item_list);
    #print rows_count, cols_count; 
    feature_value_array=[[0 for y in xrange(cols_count)] for x in xrange(rows_count)];    
    #print feature_value_array;
    
    if (rows_count>0):                                                                         
      for rows_index,item in enumerate(nuclues_item_list):       
        feature_value_list=item[2];                    
        for cols_index,feature_value in  enumerate(feature_value_list):          
          feature=feature_value[0];
          value=feature_value[1]; 
          #print rows_index,cols_index,feature,value;
          feature_value_array[rows_index][cols_index]=value;           
          
      feature_result=[];      
      for cols_index,feature in enumerate(feature_list):
        value_list=[row[cols_index] for row in feature_value_array];
        #print value_list;
        value_list=np.array(value_list)
        value_list=np.asfarray(value_list,float)
        tmp=[[],[],[]]
        if len(value_list)>0:                
          mean= np.mean(value_list);
          #print mean;
          std= np.std(value_list);
          #print std; 
        else:
          mean="n/a";
          std="n/a";
        
        tmp[0]= feature;
        tmp[1]= mean;
        tmp[2]= std     
        feature_result.append(tmp); 
        #exit();    
      #print "case_id,image_width,image_height,mpp_x,mpp_y,user,tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,tumorFlag,feature_result";
      #print case_id,image_width,image_height,mpp_x,mpp_y,user,tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,tumorFlag,feature_result;             
      saveFeatures2MongoDB(case_id,image_width,image_height,mpp_x,mpp_y,user,tile_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,tumorFlag,feature_result,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count);           
  #####################################################################
          
  print '--- process image_list  ---- ';   
  for item  in image_list:  
    case_id=item[0];
    user=item[1];  
     
    prefix_list=findPrefixList(case_id);
    if(len(prefix_list))<1:
      print "can NOT find prefix of this image!"
      exit();  
         
    comp_execution_id=getCompositeDatasetExecutionID(case_id);
    if(comp_execution_id==""):
      print "Composite dataset for this image is NOT available.";  
      continue;
    print "comp_execution_id is:" + str(comp_execution_id);
    
    humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user); 
    if(len(humanMarkupList_tumor) ==0 and humanMarkupList_non_tumor==0):
      print "No tumor or non tumor regions has been marked in this image by user %s." % user;
      continue;    
      
    #create local folder
    local_img_folder = os.path.join(local_dataset_folder, case_id);   
    if not os.path.exists(local_img_folder):
      print '%s folder do not exist, then create it.' % local_img_folder;
      os.makedirs(local_img_folder);  
       
    image_file_name=case_id+".svs";
    image_file = os.path.join(local_image_folder, image_file_name);         
    if not os.path.isfile(image_file):
      print "image svs file is not available, then download it to local folder.";
      img_path=findImagePath(case_id);
      full_image_file = os.path.join(remote_image_folder, img_path);      
      subprocess.call(['scp', full_image_file,local_image_folder]);   
       
    image_file = os.path.join(local_image_folder, image_file_name);
    print image_file;    
    try:
      img = openslide.OpenSlide(image_file);      
    except Exception as e: 
      print(e);
      continue; 
      
    image_width =img.dimensions[0];
    image_height =img.dimensions[1]; 
    #get image mpp-x and mpp-y
    for mpp_data in images.find({"case_id":case_id},{"mpp-x":1,"mpp-y":1,"_id":0}): 
      mpp_x=mpp_data["mpp-x"]; 
      mpp_y=mpp_data["mpp-y"];
      break;
    print " ==== image_width,image_height,mpp-x,mpp-p === ";
    print image_width,image_height,mpp_x,mpp_y
    
    #copy composite dataset to local folder  
    remote_img_folder = os.path.join(remote_dataset_folder, case_id);  
    for prefix in prefix_list:   
      detail_remote_folder = os.path.join(remote_img_folder, prefix); 
      detail_local_folder  = os.path.join(local_img_folder, prefix);    
      if not os.path.exists(detail_local_folder):
        print '%s folder do not exist, then create it.' % detail_local_folder;
        os.makedirs(detail_local_folder);        
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0: 
        print " all csv and json files of this image have been copied from data node.";      
      else:
        subprocess.call(['scp', detail_remote_folder+'/*.json',detail_local_folder]);
        subprocess.call(['scp', detail_remote_folder+'/*features.csv',detail_local_folder]);    
    
    unique_tile_min_point_list=findUniqueTileList(local_img_folder,prefix_list);
    print "len(unique_tile_min_point_list)";
    print len(unique_tile_min_point_list);
    
    final_total_nuclues_polygon_count=0; 
    final_invalid_nuclues_polygon_count=0;
    final_overlap_nuclues_polygon_count=0;
              
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor: 
      for index,tile_min_point in enumerate(unique_tile_min_point_list):         
        tile_width,tile_height = getTileMetaData(tile_min_point,local_img_folder,prefix_list);       
        tile_minx=tile_min_point[0];
        tile_miny=tile_min_point[1]; 
        x1t=float(tile_minx)/float(image_width);
        y1t=float(tile_miny)/float(image_height); 
        x2t=float(tile_minx+tile_width)/float(image_width);
        y2t=float(tile_miny+tile_height)/float(image_height);
        tile_polygon_0=[[x1t,y1t],[x2t,y1t],[x2t,y2t],[x1t,y2t],[x1t,y1t]];       
        x=tile_min_point[0];
        y=tile_min_point[1];
        tmp_string="_x"+str(x)+"_y" + str(y); 
        tile_item_array=[];
        for prefix in prefix_list:   
          detail_local_folder  = os.path.join(local_img_folder, prefix);
          for csv_json_file in os.listdir(detail_local_folder):   
            if csv_json_file.endswith("features.csv") and csv_json_file.find(tmp_string) <> -1:#find it! 
              tmp_obj_list=read_csv_data_file(detail_local_folder,csv_json_file);       
              tile_item_array.extend(tmp_obj_list);           
           
        i_range=tile_width/patch_size;
        j_range=tile_height/patch_size;                    
        for i in range(0,i_range):
          for j in range(0,j_range):
            x1=float(tile_minx+i*patch_size)/float(image_width);
            y1=float(tile_miny+j*patch_size)/float(image_height);
            x2=x1+float(patch_size)/float(image_width);
            y2=y1+float(patch_size)/float(image_height);            
            if x1>1.0:
              x1=1.0;
            if x1<0.0:
              x1=0.0; 
            if x2>1.0:
              x2=1.0;            
            if x2<0.0:
              x2=0.0;            
            if y1>1.0:
              y1=1.0;
            if y1<0.0:
              y1=0.0; 
            if y2>1.0:
              y2=1.0;
            if y2<0.0:
              y2=0.0;          
            patch_polygon_0=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]];            
            tmp_poly=[tuple(i1) for i1 in patch_polygon_0];
            tmp_polygon = Polygon(tmp_poly);
            patch_polygon = tmp_polygon.buffer(0); 
             
            patch_polygon_area0 =patch_polygon.area;          
            patch_polygon_area1=0.0;
            patch_polygon_area2=0.0;
            
            patchHumanMarkupRelation_tumor="disjoin";
            patchHumanMarkupRelation_nontumor="disjoin";  
            patch_humanmarkup_intersect_polygon_tumor = Polygon([(0, 0), (1, 1), (1, 0)]);
            patch_humanmarkup_intersect_polygon_nontumor = Polygon([(0, 0), (1, 1), (1, 0)]);            
            
            tumor_polygon_intersect = patch_polygon;
            non_tumor_polygon_intersect = patch_polygon;
            for humanMarkup in humanMarkupList_tumor:                         
              if (patch_polygon.within(humanMarkup)):              
                patchHumanMarkupRelation_tumor="within";
                tumor_related_patch=True;
                patch_polygon_area1=patch_polygon.area;
                break;
              elif (patch_polygon.intersects(humanMarkup)):                
                patchHumanMarkupRelation_tumor="intersect";  
                patch_humanmarkup_intersect_polygon_tumor=humanMarkup;
                tumor_related_patch=True;
                polygon_intersect=patch_polygon.intersection(humanMarkup);
                patch_polygon_area1=polygon_intersect.area;
                tumor_polygon_intersect = polygon_intersect
                break;
              else:               
                patchHumanMarkupRelation_tumor="disjoin";           
            
            for humanMarkup2 in humanMarkupList_non_tumor:                        
              if (patch_polygon.within(humanMarkup2)):              
                patchHumanMarkupRelation_nontumor="within";
                non_tumor_related_patch=True;
                patch_polygon_area2=patch_polygon.area;
                break;
              elif (patch_polygon.intersects(humanMarkup2)):                
                patchHumanMarkupRelation_nontumor="intersect";  
                patch_humanmarkup_intersect_polygon_nontumor=humanMarkup2;
                non_tumor_related_patch=True;
                polygon_intersect=patch_polygon.intersection(humanMarkup2);
                patch_polygon_area2=polygon_intersect.area;
                non_tumor_polygon_intersect = polygon_intersect;
                break;
              else:               
                patchHumanMarkupRelation_nontumor="disjoin";          
            
             
            #only calculate features within/intersect tumor/non tumor region           
            if(patchHumanMarkupRelation_tumor=="disjoin" and patchHumanMarkupRelation_nontumor=="disjoin"):                     
              continue;  
          
            patch_min_x=int(x1*image_width);
            patch_min_y=int(y1*image_height); 
            #print index,tile_min_point,patch_min_x,patch_min_y;            
            patch_area1_seleted_percentage=float((patch_polygon_area1/patch_polygon_area0)*100); 
            patch_area2_seleted_percentage=float((patch_polygon_area2/patch_polygon_area0)*100);  
            #if selected patch area is too small, skip this patch
            if patch_area1_seleted_percentage<1.0 and patch_area2_seleted_percentage <1.0:
              continue                           
            
            total_nuclues_polygon_count=0; 
            invalid_nuclues_polygon_count=0;
            overlap_nuclues_polygon_count=0;
            
            if (patch_polygon_area1>0.0 and  patch_polygon_area2==0.0): 
              nuclues_item_list_tumor=[];          
              for tile_item in tile_item_array:
                is_intersects=False;
                is_within=False;
                computer_polygon =tile_item[0]; 
                computer_polygon0 =tile_item[1];
                if (computer_polygon.within(tumor_polygon_intersect)): 
                  is_within=True;
                if (computer_polygon.intersects(tumor_polygon_intersect)): 
                  is_intersects=True;         
                if(is_within or is_intersects):
                  #filter to eliminate invalid  nuclues_polygon 
                  total_nuclues_polygon_count+=1; 
                  validity=explain_validity(computer_polygon0);            
                  if (validity=="Valid Geometry"):                                                  
                    nuclues_item_list_tumor.append(tile_item);               
                  else:
                    #print "find invalid geometry!";  
                    #print validity;
                    invalid_nuclues_polygon_count+=1
                    logging.debug('find invalid geometry.'); 
                    logging.debug(validity); 
              before_count=len(nuclues_item_list_tumor);                       
              nuclues_item_list_tumor=removeOverlapPolygon(nuclues_item_list_tumor) 
              after_count=len(nuclues_item_list_tumor); 
              overlap_nuclues_polygon_count = before_count- after_count; 
              print " --- go to tumor function ---" ;      
              executor.submit(process_one_patch,case_id,user,index,'tumor',image_width,image_height,mpp_x,mpp_y,patch_polygon_0,nuclues_item_list_tumor,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count);  
              final_total_nuclues_polygon_count+=total_nuclues_polygon_count;
              final_invalid_nuclues_polygon_count+=invalid_nuclues_polygon_count;
              final_overlap_nuclues_polygon_count+=overlap_nuclues_polygon_count;
                         
            elif (patch_polygon_area1==0.0 and  patch_polygon_area2>0.0):  
              nuclues_item_list_non_tumor=[];          
              for tile_item in tile_item_array:
                is_intersects=False;
                is_within=False;
                computer_polygon =tile_item[0]; 
                computer_polygon0 =tile_item[1];
                if (computer_polygon.within(non_tumor_polygon_intersect)): 
                  is_within=True;
                if (computer_polygon.intersects(non_tumor_polygon_intersect)): 
                  is_intersects=True;         
                if(is_within or is_intersects):
                  #filter to eliminate invalid  nuclues_polygon  
                  total_nuclues_polygon_count+=1;
                  validity=explain_validity(computer_polygon0);            
                  if (validity=="Valid Geometry"):                                                  
                    nuclues_item_list_non_tumor.append(tile_item);               
                  else:
                    #print "find invalid geometry!";  
                    #print validity;
                    invalid_nuclues_polygon_count+=1
                    logging.debug('find invalid geometry.'); 
                    logging.debug(validity); 
              before_count=len(nuclues_item_list_non_tumor);                       
              nuclues_item_list_non_tumor=removeOverlapPolygon(nuclues_item_list_non_tumor);
              after_count=len(nuclues_item_list_non_tumor); 
              overlap_nuclues_polygon_count = before_count- after_count;
              print " --- go to non_tumor function ---"          
              executor.submit(process_one_patch,case_id,user,index,'non_tumor',image_width,image_height,mpp_x,mpp_y,patch_polygon_0,nuclues_item_list_non_tumor,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count);
              final_total_nuclues_polygon_count+=total_nuclues_polygon_count;
              final_invalid_nuclues_polygon_count+=invalid_nuclues_polygon_count;
              final_overlap_nuclues_polygon_count+=overlap_nuclues_polygon_count;
                
            elif (patch_polygon_area1>0.0 and  patch_polygon_area2>0.0):  
              nuclues_item_list_tumor=[];          
              for tile_item in tile_item_array:
                is_intersects=False;
                is_within=False;
                computer_polygon =tile_item[0]; 
                computer_polygon0 =tile_item[1];
                if (computer_polygon.within(tumor_polygon_intersect)): 
                  is_within=True;
                if (computer_polygon.intersects(tumor_polygon_intersect)): 
                  is_intersects=True;         
                if(is_within or is_intersects):
                  #filter to eliminate invalid  nuclues_polygon  
                  total_nuclues_polygon_count+=1;
                  validity=explain_validity(computer_polygon0);            
                  if (validity=="Valid Geometry"):                                                  
                    nuclues_item_list_tumor.append(tile_item);               
                  else:
                    #print "find invalid geometry!";  
                    #print validity;
                    invalid_nuclues_polygon_count+=1
                    logging.debug('find invalid geometry.'); 
                    logging.debug(validity);  
              before_count=len(nuclues_item_list_tumor);                      
              nuclues_item_list_tumor=removeOverlapPolygon(nuclues_item_list_tumor) ;
              after_count=len(nuclues_item_list_tumor); 
              overlap_nuclues_polygon_count = before_count- after_count;
              print " --- go to tumor function ---"
              executor.submit(process_one_patch,case_id,user,index,'tumor',image_width,image_height,mpp_x,mpp_y,patch_polygon_0,nuclues_item_list_tumor,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count); 
              final_total_nuclues_polygon_count+=total_nuclues_polygon_count;
              final_invalid_nuclues_polygon_count+=invalid_nuclues_polygon_count;
              final_overlap_nuclues_polygon_count+=overlap_nuclues_polygon_count;
              
              total_nuclues_polygon_count=0; 
              invalid_nuclues_polygon_count=0;
              overlap_nuclues_polygon_count=0;               
              nuclues_item_list_non_tumor=[];          
              for tile_item in tile_item_array:
                is_intersects=False;
                is_within=False;
                computer_polygon =tile_item[0]; 
                computer_polygon0 =tile_item[1];
                if (computer_polygon.within(non_tumor_polygon_intersect)): 
                  is_within=True;
                if (computer_polygon.intersects(non_tumor_polygon_intersect)): 
                  is_intersects=True;         
                if(is_within or is_intersects):
                  #filter to eliminate invalid  nuclues_polygon  
                  total_nuclues_polygon_count+=1;
                  validity=explain_validity(computer_polygon0);            
                  if (validity=="Valid Geometry"):                                                  
                    nuclues_item_list_non_tumor.append(tile_item);               
                  else:
                    #print "find invalid geometry!";  
                    #print validity;
                    invalid_nuclues_polygon_count+=1
                    logging.debug('find invalid geometry.'); 
                    logging.debug(validity);  
              before_count=len(nuclues_item_list_non_tumor);                      
              nuclues_item_list_non_tumor=removeOverlapPolygon(nuclues_item_list_non_tumor);
              after_count=len(nuclues_item_list_non_tumor); 
              overlap_nuclues_polygon_count = before_count- after_count;
              print " --- go to non_tumor function ---"     
              executor.submit(process_one_patch,case_id,user,index,'non_tumor',image_width,image_height,mpp_x,mpp_y,patch_polygon_0,nuclues_item_list_non_tumor,total_nuclues_polygon_count,invalid_nuclues_polygon_count,overlap_nuclues_polygon_count); 
              final_total_nuclues_polygon_count+=total_nuclues_polygon_count;
              final_invalid_nuclues_polygon_count+=invalid_nuclues_polygon_count;
              final_overlap_nuclues_polygon_count+=overlap_nuclues_polygon_count;
            #exit();  
            
    print case_id,final_total_nuclues_polygon_count,final_invalid_nuclues_polygon_count,final_overlap_nuclues_polygon_count; 
    saveSegmentCount2MongoDB(case_id,final_total_nuclues_polygon_count,final_invalid_nuclues_polygon_count,final_overlap_nuclues_polygon_count);                                                                   
    img.close();  
  exit();  
 
