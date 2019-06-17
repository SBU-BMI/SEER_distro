import json
import os
import numpy as np
import csv
import cv2
import sys
import shutil
import subprocess
import skimage.io
import time
from datetime import datetime
import logging
import concurrent.futures 
from multiprocessing import Process
import collections
from pymongo import MongoClient
import shapely.geometry
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely import ops
from shapely.validation import explain_validity
import openslide


#######################################
def handMultiPolygon_copy(polygon_list):
  tmp_polygon_list=[];  
  for poly in polygon_list:    
    if poly.geom_type  == 'Polygon':
      tmp_polygon_list.append(poly);
    elif poly.geom_type  == 'MultiPolygon':
      allparts = [p.buffer(0) for p in poly.geometry]
      poly.geometry = shapely.ops.cascaded_union(allparts)
      ext_polygon_points =list(zip(*poly.geometry.exterior.coords.xy)); 
      newPoly = Polygon(ext_polygon_points);
      tmp_polygon_list.append(newPoly);
         
  return tmp_polygon_list;  
######################################

#######################################
def handMultiPolygon_copy2(polygon_list):
  tmp_polygon_list=[];  
  for poly in polygon_list:    
    if poly.geom_type  == 'Polygon':
      tmp_polygon_list.append(poly);
    elif poly.geom_type  == 'MultiPolygon':      
      new_shape = shapely.ops.cascaded_union(poly);
      #print new_shape.geom_type;
      if new_shape.geom_type == 'MultiPolygon':        
        for polygon in new_shape:       
          #ext_polygon_points =list(zip(*polygon.geometry.exterior.coords.xy)); 
          #newPoly = Polygon(ext_polygon_points);
          #tmp_polygon_list.append(newPoly);
          tmp_polygon_list.append(polygon);
      elif new_shape.geom_type == 'Polygon':
        tmp_polygon_list.append(new_shape);  
        
  return tmp_polygon_list;  
######################################

#######################################
def handMultiPolygon(polygon_list):
  #print "input polygon number is " + str(len(polygon_list));
  '''
  for poly_tmp in polygon_list:    
    print  poly_tmp.geom_type;
    print  poly_tmp.area;
    print  explain_validity(poly_tmp); 
    print  poly_tmp.bounds;
    print  poly_tmp; 
  '''  
  tmp_polygon_list=[];  
  for poly in polygon_list:    
    if poly.geom_type  == 'Polygon':
      tmp_polygon_list.append(poly);
    elif poly.geom_type  == 'MultiPolygon':      
      new_shape = shapely.ops.cascaded_union(poly);
      #print new_shape.geom_type;
      if new_shape.geom_type == 'MultiPolygon':   
        print  "-- find MultiPolygon --";    
        for polygon in new_shape:       
          ext_polygon_points =list(zip(*polygon.exterior.coords.xy)); 
          newPoly = Polygon(ext_polygon_points);
          tmp_polygon_list.append(newPoly);
          #tmp_polygon_list.append(polygon);
      elif new_shape.geom_type == 'Polygon':
        tmp_polygon_list.append(new_shape); 
  '''       
  print "--------------------------------"
  print "output polygon number  is " + str(len(tmp_polygon_list));
  for poly_tmp in tmp_polygon_list:    
    print  poly_tmp.geom_type;
    print  poly_tmp.area;
    print  explain_validity(poly_tmp); 
    print  poly_tmp.bounds;
    print  poly_tmp;
  '''       
  return tmp_polygon_list;  
######################################

#############################################
def findTumor_NonTumorRegions(case_id,user):
  #execution_id=user+"_Tumor_Region";
  #execution_id2=user+"_Non_Tumor_Region";
  execution_id="ardy360@gmail.com"
  execution_id2="";
  #print "case_id is:" +str(case_id);
    
  #handle only tumor region overlap
  humanMarkupList_tumor=[];
  tmp_tumor_markup_list0=[];
    
  for humarkup in objects.find({"provenance.image.case_id":case_id,
                                "provenance.analysis.execution_id":execution_id},
                               {"geometry":1,"_id":1}): 
    humarkup_polygon_tmp=humarkup["geometry"]["coordinates"][0]; 
    #print humarkup_polygon_tmp;
    #print "###########################################"
    #print humarkup_polygon_tmp;            
    tmp_polygon=[tuple(i2) for i2 in humarkup_polygon_tmp];
    tmp_polygon2=Polygon(tmp_polygon); 
    #print  tmp_polygon2.geom_type;
    original_area=tmp_polygon2.area
    #print  tmp_polygon2.area;
    #print  explain_validity(tmp_polygon2); 
    #print tmp_polygon2.is_valid
    #print  tmp_polygon2.bounds;
    #tmp_polygon2=tmp_polygon2.convex_hull;       
    tmp_polygon3=tmp_polygon2.buffer(0); 
    #print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" 
    #print  tmp_polygon3.geom_type;
    area=tmp_polygon3.area;
    #print area;
    #print explain_validity(tmp_polygon3); 
    #print tmp_polygon3.is_valid
    #print  tmp_polygon3.bounds; 
    factor=float(area)/float(original_area);
    if factor<0.5 or factor>2.0:
      print "--- find this polygon area has changed. ---";
      tmp_polygon3=tmp_polygon2.convex_hull;      
      #print tmp_polygon3.is_valid  # -> True
      #print tmp_polygon3.is_simple  # -> True
      #print tmp_polygon3.area;
      #print tmp_polygon3.bounds;
    #print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"                                               
    tmp_tumor_markup_list0.append(tmp_polygon3);
    #print tmp_tumor_markup_list0;
  #return;
          
  #handle MultiPolygon
  tmp_tumor_markup_list=handMultiPolygon(tmp_tumor_markup_list0);   
  #print "len(tmp_tumor_markup_list)"+str(len(tmp_tumor_markup_list));
  #return  tmp_tumor_markup_list;
   
  #merge polygons if applicale            
  index_intersected=[];                                
  for index1 in range(0, len(tmp_tumor_markup_list)):  
    if index1 in index_intersected :#skip polygon,which is been merged to another one
      continue;
    humarkup_polygon1=tmp_tumor_markup_list[index1];         
    is_within=False;
    is_intersect=False;
    for index2 in range(0, len(tmp_tumor_markup_list)):  
      humarkup_polygon2=tmp_tumor_markup_list[index2];
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
  #print "len(humanMarkupList_tumor) is " + str(len(humanMarkupList_tumor));
            
  #handle only non tumor region overlap
  humanMarkupList_non_tumor=[];
  tmp_non_tumor_markup_list0=[];
  for humarkup in objects.find({"provenance.image.case_id":case_id,
                                "provenance.analysis.execution_id":execution_id2},
                               {"geometry":1,"_id":0}):
    humarkup_polygon_tmp=humarkup["geometry"]["coordinates"][0];             
    tmp_polygon=[tuple(i2) for i2 in humarkup_polygon_tmp];
    tmp_polygon2=Polygon(tmp_polygon); 
    original_area=tmp_polygon2.area
    #tmp_polygon2=tmp_polygon2.convex_hull;       
    tmp_polygon3=tmp_polygon2.buffer(0);
    area=tmp_polygon3.area;
    factor=float(area)/float(original_area);
    if factor<0.5 or factor>2.0:
      print "--- find this polygon area is changed.---"
      tmp_polygon3=tmp_polygon2.convex_hull;
    tmp_non_tumor_markup_list0.append(tmp_polygon3);   
      
  #handle MultiPolygon
  tmp_non_tumor_markup_list=handMultiPolygon(tmp_non_tumor_markup_list0); 
        
  index_intersected=[];                                
  for index1 in range(0, len(tmp_non_tumor_markup_list)):  
    if index1 in index_intersected :#skip polygon,which is been merged to another one
      continue;
    humarkup_polygon1=tmp_non_tumor_markup_list[index1]; 
    is_within=False;
    is_intersect=False;
    for index2 in range(0, len(tmp_non_tumor_markup_list)):  
      humarkup_polygon2=tmp_non_tumor_markup_list[index2];
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
##############################################


##################################################
def isPatchRelated2TumorRegion(patch_record,humanMarkupList_tumor,humanMarkupList_non_tumor):
  imageW=patch_record["image_width"]; 
  imageH=patch_record["image_height"];
  patch_x=patch_record["patch_x"]; 
  patch_y=patch_record["patch_y"]; 
  patch_width=patch_record["patch_width"]; 
  patch_height=patch_record["patch_height"];
    
  x1=float(patch_x)/float(imageW);
  y1=float(patch_y)/float(imageH); 
  x2=float(patch_x+patch_width)/float(imageW);
  y2=float(patch_y+patch_height)/float(imageH);
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
  tmp_poly=[tuple(i) for i in patch_polygon_0];
  tmp_polygon = Polygon(tmp_poly);
  patch_polygon = tmp_polygon.buffer(0);
    
  patchHumanMarkupRelation_tumor="disjoin";
  patchHumanMarkupRelation_nontumor="disjoin";
    
  for humanMarkup in humanMarkupList_tumor:                         
    if (patch_polygon.within(humanMarkup)):              
      patchHumanMarkupRelation_tumor="within";        
      break;
    elif (patch_polygon.intersects(humanMarkup)):                
      patchHumanMarkupRelation_tumor="intersect";          
      break;
    else:               
      patchHumanMarkupRelation_tumor="disjoin";           
            
  for humanMarkup2 in humanMarkupList_non_tumor:                        
    if (patch_polygon.within(humanMarkup2)):              
      patchHumanMarkupRelation_nontumor="within";        
      break;
    elif (patch_polygon.intersects(humanMarkup2)):                
      patchHumanMarkupRelation_nontumor="intersect";        
      break;
    else:               
      patchHumanMarkupRelation_nontumor="disjoin";          
                      
  #only calculate features within/intersect tumor/non tumor region           
  if(patchHumanMarkupRelation_tumor=="disjoin" and patchHumanMarkupRelation_nontumor=="disjoin"):                     
    return False;            
  else: 
    return True;      
#################################################


##################################################################### 
if __name__ == "__main__":    
  if len(sys.argv)<0:
    print "usage:python add_tumor_flag.py";
    exit();       
  
  my_home="/home/bwang/patch_level";  
  code_base="/home/bwang/patch_level";      
  
  print " --- read config.json file ---" ;
  config_json_file_name = "config_seer_pdac.json";  
  config_json_file = os.path.join(code_base, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name = d['db_name'];     
    print patch_size,db_host,db_port,db_name;
    
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/',connect=False);     
  db = client[db_name];   
  
  objects = db.tumor_region;   
  patch_level_dataset= db.patch_level_radiomics_features_copy;
  
  '''
  image_list=[]; 
  #image_list.append(test_image);
  for case_id in patch_level_dataset.distinct("case_id"):
    if case_id<>test_image:
     image_list.append(case_id);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  '''  
  
  #target_image="VTRPDAC_Test_PC1125_BL1_00";
  target_image="VTRPDAC_Test_PC6725_BL1_00"  
  #target_image="VTRPDAC_Test_PC1612_BL1_XX"
  
  print '--- read image_list file ---- ';    
  image_list=[];  
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
  '''
  print "total rows from image_list file is %d " % len(image_list) ; 
  #print image_list;
  #exit();
  
  
  
  for case_id in image_list:
    #get human markup data
    user="user" 
    #print "------- process image " +str(case_id)+ " --------";     
    #humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user);    
    #total_patch_count=patch_level_dataset.find({"case_id":case_id}).count();
    #tumor_patch_count=patch_level_dataset.find({"case_id":case_id,"tumor_flag":1}).count();
    #non_tumor_patch_count=patch_level_dataset.find({"case_id":case_id,"tumor_flag":0}).count(); 
    #print "tumor_patch_count is " +str(tumor_patch_count);
    #print "non_tumor_patch_count is " +str(non_tumor_patch_count);
    #print "total_patch_count is " +str(total_patch_count);
    #continue;
         
    try:       
      humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user);      
      print "len(humanMarkupList_tumor) is " +str(len(humanMarkupList_tumor));
      print "len(humanMarkupList_non_tumor) is " +str(len(humanMarkupList_non_tumor));
      
      '''
      print "=================== after function return =========================="
      for poly_tmp in humanMarkupList_tumor:        
        print  poly_tmp.geom_type;
        print  poly_tmp.area;
        print  poly_tmp.bounds;
        #print  poly_tmp;
        print "------------------"
      '''
                
      if(len(humanMarkupList_tumor) ==0):
        print "No tumor or non tumor regions has been marked in this image by user %s." % user;
        continue; 
      
              
      print "------- process image " +str(case_id)+ " --------";         
      tumor_patch_count=0;
      non_tumor_patch_count=0;
      
      total_patch=patch_level_dataset.find({"case_id":case_id}).count();
      print "total_patch count is:" + str(total_patch);        
       
      for record in patch_level_dataset.find({"case_id":case_id}):  
        #patch_x=record["patch_x"]; 
        #patch_y=record["patch_y"];     
        return_value=isPatchRelated2TumorRegion(record,humanMarkupList_tumor,humanMarkupList_non_tumor);
        if not return_value:
          #print "process patch patch_x: " +str(patch_x) + " patch_y:" + str(patch_y);
          #print "this patch is NOT within/intersect with tumor region";
          non_tumor_patch_count+=1;
          tumor_flag=0;
        else:
          tumor_patch_count+=1;
          tumor_flag=1;
        #print record["_id"];  
        patch_level_dataset.update({"_id": record["_id"]}, {"$set": {"tumor_flag": tumor_flag}},upsert=False, multi=False);    
        #break; 
         
      print "tumor_patch_count is " +str(tumor_patch_count);
      print "non_tumor_patch_count is " +str(non_tumor_patch_count);
      #print "total_patch_count is " +str(total_patch_count);
      #break;      
      
    #except: # catch *all* exceptions
    except Exception as e:
      print "error occur in process image " +str(case_id)+ " --------";
      print e      
      continue;
      
  client.close()                                                  
  exit();      
    
