from pymongo import MongoClient
from bson.objectid import ObjectId
import subprocess
import os
import sys
import csv
import json
import collections
import datetime
import numpy as np
import matplotlib.pyplot as plt; plt.rcdefaults()
from textwrap import wrap
import fnmatch

  

if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage: python deleteDuplicate.py";
    exit();   
    
  code_base="/home/bwang/patch_level";
  
  print " --- read config file ---" ;
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
  
  tumor_region = db.tumor_region;
  
  for record in tumor_region.aggregate([{"$group": { "_id": { "x": "$x", "y": "$y" } } }]):
    #print record;  
    #print record["_id"];
    line_value=record["_id"];
    #x=line_value.x;
    #print x;
    x=0;
    y=0;
    for key, value in line_value.items():
      #print key, value;
      if key=='x':
        x=value;
      if key=='y':
        y=value;          
    return_count = tumor_region.find({"x":x,"y":y}).count();
    #print x,y,return_count;
    #print return_count,x,y;
    if return_count>0 and  x<>0 and y<>0:
      for tmp_record in tumor_region.find({"x":x,"y":y}):
        case_id=tmp_record['provenance']['image']['case_id'];
        _id=tmp_record['_id'];
        print return_count,_id,case_id,x,y;
        #tumor_region.delete_one({'_id': ObjectId(_id)});
        #break;
        
    '''  
    x=record["_id"]['x'];
    y=record["_id"]['y'];
    print x,y;
    '''  
  client.close()  
  exit();
  
  
       
  #images =db.images; 
  #metadata=db.metadata;
  #objects = db.tahsin_tumor;
  '''
  with open('tahsin_tumor.json') as f:
    file_data = json.load(f);    
    tahsin_tumor.insert(file_data);
  client.close()
  '''
  
  '''
  record_count=tahsin_tumor.find().count();
  print "record_count is :" + str(record_count);
  client.close()
  exit();
  '''
  
  '''
  pdac_image_list=[];
  for case_id in db.tahsin_tumor.distinct("provenance.image.case_id"):
    #print   case_id
    pdac_image_list.append(case_id); 
  print pdac_image_list   
  exit();
  '''  
  
  '''
  #read additional_images.txt file
  print '--- read additional_images.txt file ---- ';    
  additional_image_list=[];  
  image_list_file_name = "additional_images.txt";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                      
      case_id=each_row[0];  
      print case_id
      additional_image_list.append(case_id);                
  print "total rows from image_list file is %d " % len(additional_image_list) ; 
  #exit();
  '''  
  
  '''
  host_machine='nfs008';
  image_location_path="/data/shared/tcga_analysis/seer-pdac-segmentation/";  
  for case_id in additional_image_list:     
    target_file= str(case_id)+".svs" ;
    target_folder= str(case_id)+".svs" ;    
    imageFilePath,segmentResultPath=findImageFileAndSegmentResultPath(image_location_path,target_file,target_folder);
    print str(case_id)+ ","+str(host_machine)+":"+str(imageFilePath)+","+ str(host_machine)+":"+str(segmentResultPath); 
  exit();  
  '''
   
  #images location:
  #host_machine='nfs008';
  #login nfs008 to run this code
  #image_location_list=['/data/shared/tcga_analysis/seer-pdac-segmentation/node001/seer_cnn_runs/input_data/',
  #                     '/data/shared/tcga_analysis/seer-pdac-segmentation/node002/seer_cnn_runs/input_data/',
  #                     '/data/shared/tcga_analysis/seer-pdac-segmentation/node005/seer_cnn_runs/input_data/',
  #                     '/data/shared/tcga_analysis/seer-pdac-segmentation/node006/seer_cnn_runs/input_data/']

  #file_count=0;
  '''
  for image_location in image_location_list:
    #print image_location;
    for image_file_name in os.listdir(image_location):
      #print image_file_name;
      case_id=image_file_name.rstrip(".svs");     
      images_count=images.find({"case_id":case_id}).count();
      metadata_count=metadata.find({"image.case_id":case_id}).count();
      object_count=objects.find({"provenance.image.case_id":case_id}).count();
      print  case_id,images_count,metadata_count,object_count;
      file_count+=1;
  
  print "total image file count:" + str(file_count); 
  '''
  
  '''
  image_location_path="/data/shared/tcga_analysis/seer-pdac-segmentation/";  
  for case_id in images.distinct("case_id"):     
    target_file= str(case_id)+".svs" ;
    target_folder= str(case_id)+".svs" ;    
    imageFilePath,segmentResultPath=findImageFileAndSegmentResultPath(image_location_path,target_file,target_folder);
    print str(case_id)+ ","+str(host_machine)+":"+str(imageFilePath)+","+ str(host_machine)+":"+str(segmentResultPath); 
  exit();
  '''
  
  print '--- read image_list file ---- ';    
  image_list=[];  
  image_list_file_name = "image_list_2019_5_9";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                      
      tmp=each_row[0];      
      #image_list.append(tmp); 
      #case_id=tmp
      #patch_level_dataset = db.patch_level_radiomics_features;
      #tmp_count= patch_level_dataset.find({"case_id":case_id}).count(); 
      #if tmp_count ==0:   
      image_list.append(tmp);           
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  #exit();
  
  
  '''
  print '--- read image_list file ---- ';    
  image_list=[];  
  image_list_file_name = "seer_pdac_image_path.txt";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list: 
      tmp_item=[[],[],[]]                
      tmp_item[0]=each_row[0];  
      tmp_item[1]=each_row[1];
      tmp_item[2]=each_row[2];
      image_list.append(tmp_item);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  #print image_list;
  '''
  
  '''
  for case_id in pdac_image_list:
    findtit=False;  
    for item in image_list:
      case_id_1=item[0];
      if case_id==case_id_1:
        findtit=True; 
        break; 
    if not findtit:
      print case_id;      
  exit(); 
  '''
  
  
  '''
  #generate patch level radiomics feature dataset for all patches
  for case_id in image_list[8:9]: 
    print case_id;
    #continue;   
    record_count=db.patch_level_radiomics_features.find({"case_id":case_id}).count();
    if record_count ==0:
      tumor_count=db.tahsin_tumor.find({"provenance.image.case_id":case_id}).count();
      if tumor_count >0:#with tumor markup  region
        #imageFilePath = item[1];
        imageFilePath="nfs008:/data/shared/tcga_analysis/seer-pdac-segmentation/images/" + str(case_id)+".svs"     
        #segmentResultPath = item[2];
        segmentResultPath="nfs008:/data/shared/tcga_analysis/seer-pdac-segmentation/segmentation_results/" + str(case_id)+".svs";      
        #print case_id,imageFilePath,segmentResultPath;    
        cmd = "qsub -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs";
        #cmd = "qsub -l select=1:vnode=^node001 -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs";      
        print cmd;
        proc = subprocess.Popen(cmd, shell=True); 
        status = proc.wait() ;        
      else:
        print "No tumor markup for image " + str(case_id);  
    else: 
      print "radiomics feature of image " + str(case_id) + " has been done.";       
  exit();          
  '''
  
  
  '''
  patch_level_dataset = db.patch_level_radiomics_features;
  image_list=[];
  for case_id in patch_level_dataset.distinct("case_id"):
    image_list.append(case_id);                
    print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  exit();
  '''
    
  '''
  for case_id in images.distinct("case_id")[0:1]:
    #print case_id; 
    target_file= str(case_id)+".svs" ;
    target_folder= str(case_id)+".svs" ;
    #print target_file;
    imageFilePath,segmentResultPath=findImageFileAndSegmentResultPath(image_location_path,target_file,target_folder);
    print imageFilePath;
    print segmentResultPath; 
    cmd = "qsub -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs";
    print cmd;
    proc = subprocess.Popen(cmd, shell=True) 
    status = proc.wait() ;
  
    matches = []
    for root, dirnames, filenames in os.walk(image_location_path):
      for filename in fnmatch.filter(filenames, target_file):
        matches.append(os.path.join(root, filename))
    print matches;
    
    
    for root, dirs, filelist in os.walk(image_location_path):
      #print dirs;
      for dir in dirs:
        if dir == target_folder: # insert logic to find the folder you want 
          fullpath  =os.path.join(root, dir) # Get the full path to the file
          print  fullpath;
                   
    #break;
  '''  
  #exit();
  
  
  #collection_saved= db.patch_level_radiomics_features;
  #collection_saved= db2.patient_level_radiomics_features_statistics  
    
  '''
  #create image_list
  image_list=[];
  for case_id in collection_saved.distinct("case_id"):    
    image_list.append(case_id);    
  print "total rows from image_list1 file is %d " % len(image_list) ; 
  print image_list;
  exit();
  '''
  
  '''
  print '--- read image_list file ---- ';    
  image_list=[];
  #image_list_file_name = "image_list_seahawk";  
  image_list_file_name = "image_list_2019_1_30";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                 
      image_list.append(each_row[0]);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  #exit(); 
  '''
  
  
