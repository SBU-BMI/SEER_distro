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
  

if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python run_all_steps.py";
    exit(); 
  
  #my_home="/data1/bwang";  
  code_base="/home/bwang/patch_level";
  
  print " --- read config.json file ---" ;
  config_json_file_name = "config_seahawk.json";  
  config_json_file = os.path.join(code_base, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;
    
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/',connect=False);     
  db = client[db_name1];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;     
  
  print '--- read image_list file ---- ';    
  image_list=[];
  #image_list_file_name = "image_list_seahawk";  
  image_list_file_name = "image_list_2019_1_23";
  image_list_file = os.path.join(code_base, image_list_file_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:                 
      image_list.append(each_row[0]);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  #exit(); 
  
  step_num=1;   
  
  if step_num==1:
    #generate patch level radiomics feature dataset for all patches
    for image_id in image_list:
      print image_id;
      cmd = "qsub -v imageid=" + image_id + " run_radiomics_seahawk_all_patches.pbs";
      print cmd;
      proc = subprocess.Popen(cmd, shell=True) 
      status = proc.wait() ;
        
          
  if step_num==2:
    #step 2: generate patient level or image level radiomics feature dataset
    patch_level_dataset = db.patch_level_radiomics_features_test;
    collection_saved    = db.patient_level_radiomics_features_statistics_test;     
    feature_array=["nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation"]; 
      
    print '--- process image_list  ---- '; 
    image_count=0;
    for case_id in image_list:  
      print case_id;
      case_id=case_id.rstrip(".tif") ;
      print case_id; 
         
      dict_data = collections.OrderedDict(); 
      dict_data['case_id']=case_id;
      dict_data['datetime'] = datetime.datetime.now();    
      
      feature_data_available=False;
      for index,feature in enumerate(feature_array):         
        feature_value_array=[];         
        print feature;       
        for record in patch_level_dataset.find({"case_id":case_id,"$and":[{feature:{ "$ne": "None" }},{feature:{ "$gt": 0.0 }}]} ,{feature:1,"_id":0}):        
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
    picture_folder = os.path.join(my_home, 'seahawk_patient_level_plot'); 
    if not os.path.exists(picture_folder):
      print '%s folder do not exist, then create it.' % picture_folder;
      os.makedirs(picture_folder);
    
    patient_level_dataset = db.patient_level_radiomics_features_statistics;   
    
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
        
  if step_num==4:
    #generate patch level radiomics feature plots 
    my_home="/home/bwang/patch_level";  
    picture_folder = os.path.join(my_home, 'seahawk_patch_level_plot'); 
    if not os.path.exists(picture_folder):
      print '%s folder do not exist, then create it.' % picture_folder;
      os.makedirs(picture_folder);
      
    patch_level_dataset = db.patch_level_radiomics_features;  
    patch_level_histogram = db.radiomics_features_histogram;
    
    image_array=[];  
    for record in patch_level_dataset.distinct("case_id"):    
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
          for record in patch_level_dataset.find({"case_id":case_id,"$and":[{feature:{ "$ne": "None" }},{feature:{ "$gt": 0.0 }}]} ,{feature:1,"_id":0}):        
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
    csv_folder = os.path.join(my_home, 'seahawk_patch_level_csv'); 
    if not os.path.exists(csv_folder):
      print '%s folder do not exist, then create it.' % csv_folder;
      os.makedirs(csv_folder);    
    patch_level_dataset = db.patch_level_radiomics_features;       
    
    feature_array=["case_id","image_width","image_height","mpp_x","mpp_y","patch_x","patch_y","patch_width","patch_height","patch_area_micro","nuclei_area_micro","nuclei_ratio","nucleus_material_percentage","nuclei_average_area","nuclei_average_perimeter","pseud_feat","fg_glcm_Autocorrelation","fg_firstorder_90Percentile","fg_firstorder_Maximum","bg_firstorder_Energy","fg_firstorder_10Percentile","fg_firstorder_Entropy","bg_firstorder_RootMeanSquared","bg_firstorder_90Percentile","bg_glcm_Correlation","fg_firstorder_RootMeanSquared","fg_firstorder_Mean","fg_firstorder_Energy","fg_glcm_Correlation","bg_firstorder_10Percentile","fg_firstorder_Median","bg_firstorder_Kurtosis","bg_firstorder_Maximum","fg_firstorder_Kurtosis","bg_firstorder_Entropy","bg_firstorder_Mean","bg_firstorder_Median","bg_glcm_Autocorrelation","datetime"];   
  
    image_array=[];  
    for record in patch_level_dataset.distinct("case_id"):    
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
          for record in patch_level_dataset.find({"case_id":case_id} ,{"_id":0}):
            row=[];
            for feature in feature_array:
              feature_value=record[feature];          
              row.append(feature_value);        
            csv_writer.writerow(row)    
                          
  exit();     
  
       
