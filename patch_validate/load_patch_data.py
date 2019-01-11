from pymongo import MongoClient
import os
import sys
import csv
import json
import random
from datetime import datetime
import collections


if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python loadPatch_level_data.py";
    exit();  
  
  db_host = "129.49.249.175";
  db_port = "27017";
  db_name1 = "quip"; 
  db_name2 = "quip_comp";  
    
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/',connect=False); 
  db1 = client[db_name1];   
  images1 =db1.images; 
  metadata1=db1.metadata;
  objects1 = db1.objects;  
  
  db2 = client[db_name2];
  images2 =db2.images; 
  metadata2=db2.metadata;
  objects2 = db2.objects;  
  
  remote_db_host="quip3.bmi.stonybrook.edu" 
  client_quip3 = MongoClient('mongodb://'+remote_db_host+':'+db_port+'/',connect=False); 
  db_quip3 = client_quip3[db_name2];
  images_quip3=db_quip3.images;
  metadata_quip3=db_quip3.metadata;
  objects_quip3 = db_quip3.objects;   
  
  
  collect_name1=db2.validation_image_list;
  collect_name2=db2.validation_radiomics_features;
  
  #get image_list
  image_list=[]
  for record in collect_name1.find():     
    case_id=record['case_id'] 
    image_list.append(case_id);
    
  for case_id in image_list:   
    count=images1.find({"case_id":case_id}).count();
    if count ==0:
      print  case_id, count;
      count2=images_quip3.find({"case_id":case_id}).count();
      print  count2;
      #for record in images_quip3.find({"case_id":case_id},{"_id":0}):
        #images1.insert_one(record);
     
  '''
  #populate patch_location entry in matadata collection
  for record in collect_name1.find():
    #print record; 
    case_id=record['case_id']    
    count=metadata1.find({"image.case_id":case_id,"provenance.analysis_execution_id":"patch_location"}).count();
    if count > 0:
      continue;
    print case_id;  
    dict_patch = collections.OrderedDict();
    dict_patch['title'] = 'patch_location'
    
    dict_provenance = {}
    dict_provenance['analysis_execution_id'] = 'patch_location'
    dict_provenance['type'] = 'human'
    dict_patch['provenance'] = dict_provenance  
       
    dict_image = {}
    dict_image['case_id'] = case_id
    dict_image['subject_id'] = case_id
    dict_patch['image'] = dict_image       
    metadata1.insert_one(dict_patch);   
  '''
  
  ''' 
  #populate patch_segment entry in matadata collection   
  for record in collect_name1.find():
    #print record; 
    case_id=record['case_id']    
    count=metadata1.find({"image.case_id":case_id,"provenance.analysis_execution_id":"patch_segment"}).count();
    if count > 0:
      continue;
    print case_id;  
    dict_patch = collections.OrderedDict();
    dict_patch['title'] = 'patch_segment'
    
    dict_provenance = {}
    dict_provenance['analysis_execution_id'] = 'patch_segment'
    dict_provenance['type'] = 'human'
    dict_patch['provenance'] = dict_provenance   
     
    dict_image = {}
    dict_image['case_id'] = case_id
    dict_image['subject_id'] = case_id
    dict_patch['image'] = dict_image       
    metadata1.insert_one(dict_patch); 
  '''    
    
  ''' 
  #populate patch_location entry in objects collection   
  for record in collect_name2.find():
    #print record; 
    case_id=record['case_id'] 
    patch_x=record['patch_x'] 
    patch_y=record['patch_y'] 
    patch_width=record['patch_width'] 
    patch_height=record['patch_height'] 
    image_width=record['image_width'] 
    image_height=record['image_height']    
    
    x1=float(patch_x)/float(image_width);
    y1=float(patch_y)/float(image_height); 
    x2=float(patch_x+patch_width)/float(image_width);
    y2=float(patch_y+patch_height)/float(image_height);
    print case_id;  
    print x1,x2,y1,y2;
    #continue;
    
    dict_patch = collections.OrderedDict();
    dict_patch['type'] = 'Feature'
    dict_patch['parent_id'] = 'self'
    dict_patch['randval'] = random.randrange(0.0,1.0)   
    dict_geo = {}
    dict_geo['type'] = 'Polygon'
    dict_geo['coordinates'] = [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]]
    dict_patch['geometry'] = dict_geo
    
    dict_patch['normalized'] = True 
    dict_patch['object_type'] = 'annotation' 
    dict_patch['footprint'] = 1.0         
    
    dict_analysis = {}
    dict_analysis['execution_id'] = 'patch_location'
    dict_analysis['study_id'] = ''
    dict_analysis['source'] = 'human'
    dict_analysis['computation'] = 'segmentation'
    
    dict_image = {}
    dict_image['case_id'] = case_id
    dict_image['subject_id'] = case_id 
    
    dict_provenance = {}
    dict_provenance['analysis'] = dict_analysis
    dict_provenance['image'] = dict_image
    dict_patch['provenance'] = dict_provenance 
    
    dict_patch['date'] = datetime.now();
    dict_patch['x'] = x1
    dict_patch['y'] = y1
             
    objects1.insert_one(dict_patch);   
  '''
  
  '''
  margin=1.0
  for case_id in image_list[1:]: 
    for meta_record in metadata_quip3.find({"image.case_id":case_id,
                                            "provenance.analysis_execution_id":{'$regex' : '_composite_dataset', '$options' : 'i'}
                                            },{"_id":0,"provenance.analysis_execution_id":1}):
      #print meta_record;                                      
      execution_id = meta_record['provenance']['analysis_execution_id'];     
      break;      
    print case_id,execution_id;
    print "-------";
    
    for objects_record in objects1.find({"provenance.image.case_id":case_id,
                                         "provenance.image.case_id":case_id,                    
                                         "provenance.analysis.execution_id":"patch_location"}):
      polygon=objects_record['geometry']['coordinates'][0];
      x1=polygon[0][0]; 
      y1=polygon[0][1];
      x2=polygon[2][0];
      y2=polygon[2][1]; 
      #print x1,y1,x2,y2;
      #print "#################";
      patch_width=x2-x1;
      patch_height=y2-y1;
      x1_new=x1-patch_width*margin;
      y1_new=y1-patch_height*margin;
      x2_new=x2+patch_width*margin;
      y2_new=y2+patch_height*margin; 
      print x1_new,y1_new,x2_new,y2_new;        
      counter=0;
      for objects_record2 in objects_quip3.find({"provenance.image.case_id":case_id,
                                                 "provenance.image.case_id":case_id,  
                                                  "x" : { '$gte':x1_new, '$lte':x2_new},
                                                  "y" : { '$gte':y1_new, '$lte':y2_new},                  
                                                 "provenance.analysis.execution_id":execution_id},
                                                 {"_id":0}): 
        #print  objects_record2; 
        objects_record2['provenance']['analysis']['execution_id']="patch_segment" ;
        #print objects_record2 
        counter+=1;        
        objects1.insert_one(objects_record2);         
      print counter;                                               
      print "====================="      
  '''      
  
            
  exit();    
 
                     
    
  
