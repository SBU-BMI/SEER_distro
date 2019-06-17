from pymongo import MongoClient
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

############################################
def findImageFileAndSegmentResultPath(root_path,target_file,target_folder):
  imageFilePath="";
  segmentResultPath="";
  
  for root, dirnames, filenames in os.walk(root_path):
    for filename in fnmatch.filter(filenames, target_file):
        imageFilePath=os.path.join(root, filename);
        break;
    else:
        # Continue if the inner loop wasn't broken.
        continue
    # Inner loop was broken, break the outer.
    break
            
  for root, dirs, filelist in os.walk(root_path):
    for dir in dirs:
      if dir == target_folder: 
          segmentResultPath =os.path.join(root, dir) ;
    else:
        # Continue if the inner loop wasn't broken.
        continue
    # Inner loop was broken, break the outer.
    break                 
        
  #print imageFilePath, segmentResultPath;  
  return imageFilePath, segmentResultPath;
###########################################
  

if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python run_all_steps_seer_pdac.py";
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
  
  #tahsin_tumor = db.tahsin_tumor       
  #images =db.images; 
  #metadata=db.metadata;
  #objects = db.tahsin_tumor;
  '''
  with open('tahsin_tumor.json') as f:
    file_data = json.load(f);    
    tahsin_tumor.insert(file_data);
  #client.close()
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
  
  '''
  print '--- read image_list file ---- ';    
  image_list=[];  
  image_list_file_name = "image_list_2019_5_20";
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
  
  
  '''
  exclude_image="VTRPDAC_Test_PC3896_BL1_XX";
  image_list=[];
  for case_id in db.patch_level_radiomics_features.distinct("case_id"):
    if case_id<>exclude_image:
      image_list.append(case_id);
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;  
  #exit();
  
  
  #generate patch level radiomics feature dataset for all patches
  for case_id in image_list: 
    print case_id;
    tumor_count=db.tumor_region.find({"provenance.image.case_id":case_id}).count();
    if tumor_count >0:#with tumor markup  region      
      imageFilePath="nfs008:/data/shared/tcga_analysis/seer-pdac-segmentation/images/" + str(case_id)+".svs"       
      segmentResultPath="nfs008:/data/shared/tcga_analysis/seer-pdac-segmentation/segmentation_results/" + str(case_id)+".svs";      
      #print case_id,imageFilePath,segmentResultPath;    
      #cmd = "qsub -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs";
      cmd = "qsub -l select=1:vnode=^node001 -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs"; 
      #cmd = "python run_radiomics_seer_pdac_all_patches.py  " + case_id + " "+ imageFilePath +" " +segmentResultPath;     
      print cmd;
      proc = subprocess.Popen(cmd, shell=True); 
      status = proc.wait() ; 
      #python run_radiomics_seer_pdac_all_patches.py  $case_id $imageFilePath $segmentResultPath  
      #os.system('python run_radiomics_seer_pdac_all_patches.py  $case_id $imageFilePath $segmentResultPath');    
    else:
      print "No tumor markup for image " + str(case_id);           
  exit();  
  '''
  
  '''
  #generate patch level radiomics feature dataset for all patches
  for case_id in image_list: 
    print case_id;
    tumor_count=db.tumor_region.find({"provenance.image.case_id":case_id}).count();
    if tumor_count >0:#with tumor markup  region      
      imageFilePath="nfs008:/data/shared/tcga_analysis/seer-pdac-segmentation/images/" + str(case_id)+".svs"       
      segmentResultPath="nfs008:/data/shared/tcga_analysis/seer-pdac-segmentation/segmentation_results/" + str(case_id)+".svs";      
      #print case_id,imageFilePath,segmentResultPath;    
      #cmd = "qsub -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs";
      #cmd = "qsub -l select=1:vnode=^node001 -v case_id=" + case_id + ",imageFilePath="+ imageFilePath +",segmentResultPath=" +segmentResultPath + " run_radiomics_seer_pdac_all_patches.pbs"; 
      cmd = "python run_radiomics_seer_pdac_all_patches.py  " + case_id + " "+ imageFilePath +" " +segmentResultPath;     
      print cmd;
      proc = subprocess.Popen(cmd, shell=True); 
      status = proc.wait() ; 
      #python run_radiomics_seer_pdac_all_patches.py  $case_id $imageFilePath $segmentResultPath  
      #os.system('python run_radiomics_seer_pdac_all_patches.py  $case_id $imageFilePath $segmentResultPath');    
    else:
      print "No tumor markup for image " + str(case_id);           
  exit();   
  '''
  
  
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
  
  
  print '--- read image_list file ---- ';    
  image_list=[];    
  image_list_file_name = "image_list_2019_6_12_2";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                 
      image_list.append(each_row[0]);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  #exit(); 
 
  
  ##########  select step ####################
  step_num=5;  
  #########################################  
  '''
  if step_num==1:
    for image_id in image_list2:
      if  image_id not in image_list1:
        print image_id;
        cmd = "qsub -v imageid=" + image_id + " run_radiomics_seahawk_all_patches.pbs";
        print cmd;
        proc = subprocess.Popen(cmd, shell=True) 
        status = proc.wait() ;
  '''
  
  if step_num==1:
    #generate patch level radiomics feature dataset for all patches
    for image_id in image_list:
      print image_id;
      cmd = "qsub -v imageid=" + image_id + " run_radiomics_seer_pdac_all_patches.pbs";
      print cmd;
      proc = subprocess.Popen(cmd, shell=True) 
      status = proc.wait() ;        
          
  if step_num==2:
    #step 2: generate patient level or image level radiomics feature dataset
    patch_level_dataset = db.patch_level_radiomics_features;
    collection_saved    = db.patient_level_radiomics_features_statistics;     
    feature_array=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"];     
    image_list=[];
    for case_id in patch_level_dataset.distinct("case_id"):    
      image_list.append(case_id);    
    print "total rows from image_list1 file is %d " % len(image_list) ; 
    print image_list;
    
    print '--- process image_list  ---- '; 
    image_count=0;
    for case_id in image_list:  
      print "----------  " + str(case_id) + "  -----------";
      #case_id=case_id.rstrip(".tif") ;
      #print case_id; 
         
      dict_data = collections.OrderedDict(); 
      dict_data['case_id']=case_id;
      dict_data['datetime'] = datetime.datetime.now();    
      
      feature_data_available=False;
      for index,feature in enumerate(feature_array):         
        feature_value_array=[];         
        print feature;       
        for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1,"$and":[{feature:{ "$ne": "None" }},{feature:{ "$gt": 0.0 }}]} ,{feature:1,"_id":0}):        
            feature_value=record[feature];
            feature_value_array.append(feature_value); 
     
        if  len(feature_value_array) <1: 
          continue;
        else:
          feature_data_available=True;
          print len(feature_value_array);
            
        dict_feature = {}      
        dict_feature['10th'] = np.percentile(feature_value_array,10);
        dict_feature['25th'] = np.percentile(feature_value_array,25);
        dict_feature['50th'] = np.percentile(feature_value_array,50); 
        dict_feature['75th'] = np.percentile(feature_value_array,75);
        dict_feature['90th'] = np.percentile(feature_value_array,90);   
        dict_data[feature] = dict_feature;    
          
      if feature_data_available:         
       collection_saved.insert_one(dict_data); 
       image_count+=1;
       print image_count
    print "total images is  %d" % image_count   
    
  if step_num==3:
    #generate patient level or image level radiomics feature plots    
    my_home="/home/bwang/patch_level";  
    picture_folder = os.path.join(my_home, 'seer_pdac_patient_level_plot'); 
    if not os.path.exists(picture_folder):
      print '%s folder do not exist, then create it.' % picture_folder;
      os.makedirs(picture_folder);
    
    patient_level_dataset = db.patient_level_radiomics_features_statistics; 
    #patch_level_dataset = db.patch_level_radiomics_features;  
    #image_list=[];
    #for case_id in patch_level_dataset.distinct("case_id"):    
    #  image_list.append(case_id);    
    #print "total rows from image_list1 file is %d " % len(image_list) ; 
    
    feature_array=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"];
  
    for record in patient_level_dataset.find({},{"_id":0}):
      case_id=record["case_id"];
      if not case_id in image_list :
        continue;
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
        
  if step_num==4:
    #generate patch level radiomics feature plots 
    my_home="/home/bwang/patch_level";  
    picture_folder = os.path.join(my_home, 'seer_pdac_patch_level_plot'); 
    if not os.path.exists(picture_folder):
      print '%s folder do not exist, then create it.' % picture_folder;
      os.makedirs(picture_folder);
      
    #patch_level_dataset = db.patch_level_radiomics_features; 
    patch_level_dataset = db.patch_level_radiomics_features; 
    patch_level_histogram = db.radiomics_features_histogram;
    
    image_array=[];  
    for record in patch_level_dataset.distinct("case_id"):  
      if not record in image_list :
        continue;  
      image_array.append(record);       
  
    feature_array=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","pseud_feat","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"];   

    name_array=["nucleus_material_percentage (%)","nuclei_average_area (square micron)","nuclei_average_perimeter (micron)","pseud_feat","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"]; 

    data_range="patch_level";
    for case_id in image_array:
      picture_folder2 = os.path.join(picture_folder, case_id); 
      if not os.path.exists(picture_folder2):
        print '%s folder do not exist, then create it.' % picture_folder2;
        os.makedirs(picture_folder2);
      else:
        continue;#done it before,skip this record
        
      for index,feature in enumerate(feature_array):         
        feature_value_array=[];   
        hist_count_array=[];
        bin_edges_array=[];
      
        if feature=="pseud_feat":
          for record in patch_level_dataset.find({"case_id":case_id} ,{feature:1,"_id":0}):
            #print record;
            feature_value=int(record["pseud_feat"]);
            feature_value_array.append(feature_value);            
        else:      
          for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1,"$and":[{feature:{ "$ne": "None" }},{feature:{ "$gt": 0.0 }}]} ,{feature:1,"_id":0}):        
            feature_value=record[feature];
            feature_value_array.append(feature_value); 
          
        print case_id,feature;       
        total_patch_count=len(feature_value_array); 
        if len(feature_value_array) >0: 
          fig, ax = plt.subplots();    
          n, bins, patches = plt.hist(feature_value_array, bins='auto',facecolor='blue');      
          plt.xlabel(name_array[index])
          plt.ylabel('Patch Count')
          plt.title("\n".join(wrap("patch level "+ feature+ ' Histogram of image '+ str(case_id))))
          #Tweak spacing to prevent clipping of ylabel
          plt.subplots_adjust(left=0.15)
          plt.grid(True);           
          # place a text box in upper left in axes coords
          props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
          total_patch_count="{:,}".format(total_patch_count)
          textstr="Total patch count: " + str(total_patch_count);
          ax.text(0.6, 0.95, textstr, transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=props);      
          #plt.show();
          file_name="patch_level_histogram_"+case_id+"_"+feature+".png";  
          graphic_file_path = os.path.join(picture_folder2, file_name);
          plt.savefig(graphic_file_path); 
          plt.gcf().clear(); 
          plt.close('all');
          #save result to database
          for count in n:        
            hist_count_array.append(int(count));
          for bin_edge in bins:        
            bin_edges_array.append(float(bin_edge));   
          saveHistogram(case_id,feature,data_range,hist_count_array,bin_edges_array);      


  if step_num==5:
    #generate patch level radiomics feature csv data file 
    my_home="/home/bwang/patch_level";
    csv_folder = os.path.join(my_home, 'tmp_patch_level_csv'); 
    if not os.path.exists(csv_folder):
      print '%s folder do not exist, then create it.' % csv_folder;
      os.makedirs(csv_folder);      
    patch_level_dataset = db.patch_level_radiomics_features_copy;     
    
    feature_array=["case_id","image_width","image_height","mpp_x","mpp_y","patch_x","patch_y","patch_width","patch_height","patch_area_micro","nuclei_area_micro","nuclei_ratio","nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","pseud_feat","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation","datetime"];   
  
    image_array=[];  
    for record in patch_level_dataset.distinct("case_id"): 
      if not record in image_list :
        continue;   
      image_array.append(record);
       
    for case_id in image_array:           
      file_name="patch_level_radiomics_feature_"+case_id+".csv";
      print "create file "+str(file_name);
      is_new_file=False;    
      if os.path.isdir(csv_folder) and len(os.listdir(csv_folder)) > 0:                            
        csv_filename_list = [f for f in os.listdir(csv_folder) if f.endswith('.csv')] ;  
        if file_name not in csv_filename_list: 
          is_new_file=True;
      elif os.path.isdir(csv_folder) and len(os.listdir(csv_folder)) == 0:    
        is_new_file=True;
    
      if is_new_file:          
        csv_dest_file = os.path.join(csv_folder, file_name);
        with open(csv_dest_file, 'wb') as csv_write: 
          csv_writer = csv.writer(csv_write);
          csv_writer.writerow(feature_array);           
          for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1} ,{"_id":0}):
            row=[];
            for feature in feature_array:
              feature_value=record[feature];          
              row.append(feature_value);        
            csv_writer.writerow(row)    

  if step_num==6:
    #generate patient level radiomics feature csv data file 
    my_home="/home/bwang/patch_level";
    csv_folder = os.path.join(my_home, 'seer_pdac_patient_level_csv'); 
    if not os.path.exists(csv_folder):
      print '%s folder do not exist, then create it.' % csv_folder;
      os.makedirs(csv_folder);  
        
    #patient_level_dataset = db2.patient_level_radiomics_features_statistics;       
    patient_level_dataset = db.patient_level_radiomics_features_statistics;
    
    feature_array=[];
    feature_array1=["case_id"]
    feature_array2=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"];   
    
    for feature in feature_array1:
      feature_array.append(feature) ;
      
    for feature in  feature_array2: 
      tmp_feature1=str(feature)+ "(10th)" 
      feature_array.append(tmp_feature1) ;
      tmp_feature2=str(feature)+ "(25th)" 
      feature_array.append(tmp_feature2) ;
      tmp_feature3=str(feature)+ "(50th)" 
      feature_array.append(tmp_feature3) ;
      tmp_feature4=str(feature)+ "(75th)" 
      feature_array.append(tmp_feature4) ;
      tmp_feature5=str(feature)+ "(90th)" 
      feature_array.append(tmp_feature5) ;
      
    image_array=[];  
    for record in patient_level_dataset.distinct("case_id"):  
      if not record in image_list :
        continue;  
      image_array.append(record);
       
    for case_id in image_array:           
      file_name="patient_level_radiomics_feature_"+case_id+".csv";
      print "create file "+str(file_name);
      is_new_file=False;    
      if os.path.isdir(csv_folder) and len(os.listdir(csv_folder)) > 0:                            
        csv_filename_list = [f for f in os.listdir(csv_folder) if f.endswith('.csv')] ;  
        if file_name not in csv_filename_list: 
          is_new_file=True;
      elif os.path.isdir(csv_folder) and len(os.listdir(csv_folder)) == 0:    
        is_new_file=True;
    
      if is_new_file:          
        csv_dest_file = os.path.join(csv_folder, file_name);
        with open(csv_dest_file, 'wb') as csv_write: 
          csv_writer = csv.writer(csv_write);
          csv_writer.writerow(feature_array);           
          for record in patient_level_dataset.find({"case_id":case_id} ,{"_id":0}):
            row=[];
            for feature in feature_array1:
              feature_value=record[feature];          
              row.append(feature_value); 
              
            for feature in feature_array2:
              try:
                feature_value=record[feature];
              except Exception as e:
                print e;
                row.append('');
                row.append('');
                row.append('');
                row.append('');
                row.append('');
                continue;              
              #feature_value=record[feature];              
              feature_value_10th =  feature_value['10th']        
              row.append(feature_value_10th); 
              feature_value_25th =  feature_value['25th']        
              row.append(feature_value_25th);
              feature_value_50th =  feature_value['50th']        
              row.append(feature_value_50th);
              feature_value_75th =  feature_value['75th']        
              row.append(feature_value_75th);
              feature_value_90th =  feature_value['90th']        
              row.append(feature_value_90th);   
                    
            csv_writer.writerow(row) 
            
  if step_num==7:
    #generate image_level_nuclei_ratio csv file 
    my_home="/home/bwang/patch_level";  
    picture_folder = os.path.join(my_home, 'seer_pdac_image_level_csv3'); 
    if not os.path.exists(picture_folder):
      print '%s folder do not exist, then create it.' % picture_folder;
      os.makedirs(picture_folder);      
   
    patch_level_dataset = db.patch_level_radiomics_features;      
    image_array=[];  
    for case_id in patch_level_dataset.distinct("case_id"):  
      #if not record in image_list :
      #  continue;  
      image_array.append(case_id); 
    
    file_name="image_level_nuclei_ratio.csv";     
    #feature_array=["case_id","total_nuclei_area_micro","total_tumor_area_micro","total_patch_area_micro","nuclei_tumor_ratio","nuclei_patch_ratio"];    
    feature_array=["case_id","total_nuclei_area_micro","total_tumor_area_micro","nuclei_tumor_ratio"]; 
    
    csv_dest_file = os.path.join(picture_folder, file_name);
    with open(csv_dest_file, 'wb') as csv_write: 
      csv_writer = csv.writer(csv_write);
      csv_writer.writerow(feature_array);             
      for case_id in image_array:    
        total_nuclei_area_micro=0.0;
        total_tumor_area_micro=0.0;
        total_patch_area_micro=0.0;    
        #for record in patch_level_dataset.find({"case_id":case_id} ,{"_id":0}):
        for record in patch_level_dataset.find({"case_id":case_id,"tumor_flag":1,"$and":[{"nuclei_ratio":{ "$ne": "None" }},{"nuclei_ratio":{ "$gt": 0.0 }}]}):
            nuclei_ratio=record['nuclei_ratio'];          
            nuclei_area_micro=record['nuclei_area_micro'];
            if nuclei_ratio==0.0:
              print case_id,nuclei_ratio;
              tumor_area_micro=patch_area_micro;
            else:
              tumor_area_micro=nuclei_area_micro/nuclei_ratio;
            
            patch_area_micro=record['patch_area_micro'];   
            total_nuclei_area_micro=total_nuclei_area_micro+nuclei_area_micro;  
            total_tumor_area_micro=total_tumor_area_micro+ tumor_area_micro;
            total_patch_area_micro=total_patch_area_micro+patch_area_micro;                   
        nuclei_tumor_ratio = total_nuclei_area_micro/ total_tumor_area_micro;
        nuclei_patch_ratio = total_nuclei_area_micro / total_patch_area_micro;
        row=[];
        row.append(case_id); 
        row.append(total_nuclei_area_micro);
        row.append(total_tumor_area_micro);
        #row.append(total_patch_area_micro);
        row.append(nuclei_tumor_ratio);
        #row.append(nuclei_patch_ratio);
        csv_writer.writerow(row);     
      
      
  if step_num==8:
    #justify some vtr image radiomics feature record count 
    radiomics_dataset1 = db2.patch_level_radiomics_features;    
    radiomics_dataset2 = db2.patch_level_radiomics_features_rerun;
    image_list=['17039895','17039896','17039844','17033057','17039843','17039878','17039901','17039885','17039851','17039877','17039845','17033063','17032591','17039841','17039842','17039847','17039856','17039793','17039794','17039920','17039833','17039834','17032584','BC_184_1_1','BC_057_0_1','BC_067_0_2','BC_378_1_1','PC_065_0_2','PC_058_2_1','BC_514_1_1'];
    for case_id in image_list:
      record_count1= radiomics_dataset1.find({"case_id":case_id}).count();  
      record_count2= radiomics_dataset2.find({"case_id":case_id}).count();
      print case_id,record_count1,record_count2;

  if step_num==9:
    #justify some vtr image radiomics feature record count 
    radiomics_dataset1 = db.patch_level_radiomics_features;    
    radiomics_dataset2 = db.patch_level_radiomics_features_run2;
    
    for case_id in radiomics_dataset2.distinct("case_id"):
      #print case_id;
      record_count=radiomics_dataset1.find({"case_id":case_id}).count();
      print case_id,record_count;    
                                             
  exit();    
  
       
