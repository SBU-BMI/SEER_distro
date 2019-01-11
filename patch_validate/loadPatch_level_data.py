from pymongo import MongoClient
import os
import sys
import csv
import json
import random
from datetime import datetime
import collections
import fnmatch
import subprocess

#######################################
def findImagePath(case_id):
  image_path="";  
  input_file="image_path.txt"
  image_path_file = os.path.join(code_base, input_file); 
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
  db_quip3 = client_quip3[db_name1];
  metadata_quip3=db_quip3.metadata;
  objects_quip3 = db_quip3.objects;   
  
  
  collect_name1=db2.validation_image_list;
  collect_name2=db2.validation_radiomics_features;
  
  my_home="/home/feiqiao/quip_install_on_2019_1_3/radiomics_validate/";
  code_base="/home/feiqiao/quip_install_on_2019_1_3/radiomics_validate/";
  
  local_image_folder="/home/feiqiao/quip2/img";
  remote_image_folder  ="bwang@eagle.bmi.stonybrook.edu:/data01/shared/tcga_analysis/seer_data/images";
  
  image_list_filename = "image_list_2019_1_11";  
  
  image_list_file = os.path.join(my_home, image_list_filename);
   
  print '--- read image_list file ---- ';    
  image_list=[];  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                 
      image_list.append(each_row[0]);                
  #print "total rows from image_list file is %d " % len(image_list) ; 
  #print image_list;
  #exit();
  
  
  
  '''
  matches = []
  for case_id in image_list:
    image_file_name=case_id+".svs";
    for root, dirnames, filenames in os.walk(local_image_folder):
      #print root, dirnames, filenames;    
      for filename in fnmatch.filter(filenames, image_file_name):
        matches.append(os.path.join(root, filename));
        print matches  
  '''
  
  
  
  for case_id in image_list[1:]:
    image_file_name=case_id+".svs";
    image_file = os.path.join(local_image_folder, image_file_name); 
    if not os.path.isfile(image_file):
      print image_file_name;
      print "image svs file is not available, then download it to local folder.";
      img_path=findImagePath(case_id);
      full_image_file = os.path.join(remote_image_folder, img_path);  
      print  full_image_file;
      subprocess.call(['scp', full_image_file,local_image_folder]);   
     
  exit();
  
    
  '''
  #get image_list
  image_list=[]
  for record in collect_name1.find():     
    case_id=record['case_id'] 
    image_list.append(case_id);
    
  for case_id in image_list:   
    count=images1.find({"case_id":case_id}).count();
    if count ==0:
      print  case_id, count;
      count2=metadata1.find({"image.case_id":case_id}).count();
      print  count2;
  '''
    
       
      
      
  '''
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
  for record in collect_name1.find():     
    case_id=record['case_id'] 
    print  case_id;  
    for meta_record in metadata_quip3.find({"image.case_id":case_id,
                                            "provenance.analysis_execution_id":{'$regex' : '_composite_dataset', '$options' : 'i'}
                                            },{"_id":0,"provenance.analysis_execution_id":1}):
      execution_id = meta_record['provenance.analysis_execution_id'];                    
      print case_id,execution_id;
      print "-------";
  '''  
  
    
  '''
  db.metadata.find({"image.case_id":"17032548",
                  "provenance.analysis_execution_id":{'$regex' : '_composite_dataset', '$options' : 'i'}},
                  {"_id":0,"provenance.analysis_execution_id":1});
                  
 

  helen.wong_composite_dataset
                
  db.objects.find({"provenance.image.case_id":"17032548",
                   "provenance.image.case_id":"17032548",
                    x : { '$gte':0.4, '$lte':0.8},
                    y : { '$gte':0.5, '$lte':0.9},
                   "provenance.analysis.execution_id":"helen.wong_composite_dataset"});  
  '''
                     
    
  '''
  #populate collection validation_image_list
  for case_id in image_list:
    #print case_id;    
    mydict = { "case_id": case_id, "date_time": datetime.now() }
    x =db2[collect_name1].insert_one(mydict);
    #print x;
  #exit();
  '''
  
  '''
  #populate collection validation_radiomics_features
  for case_id in image_list: 
    count=features_collection.find({"case_id":case_id}).count();      
    print case_id,count;
    rand_array=[];
    record_count_per_image=10;
    for i in range(0, record_count_per_image):
      rand=random.randrange(count);
      rand_array.append(rand);
    
    for ran in rand_array:
      record=features_collection.find({"case_id" : case_id},{"_id":0}).limit(-1).skip(ran).next();  
      patch_x=record["patch_x"];
      patch_y=record["patch_y"];
      patch_width=record["patch_width"];
      patch_height=record["patch_height"];
      has_tumor=record["has_tumor"];
      nuclei_ratio=record["nuclei_ratio"];
      nuclei_average_area=record["nuclei_average_area"];
      nuclei_average_perimeter=record["nuclei_average_perimeter"];
      print case_id,patch_x,patch_y,patch_width,patch_height,has_tumor,nuclei_ratio, nuclei_average_area, nuclei_average_perimeter;
      db2[collect_name2].insert_one(record);     
    #break;
  '''
      
 #exit();     
  
   
  
    
    