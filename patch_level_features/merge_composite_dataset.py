import csv
import sys
import os
import shutil
import subprocess
import json
from zipfile import ZipFile

    
#login quip3 server to run this code
    
if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python merge_composite_dataset.py";
    exit();  
  
  csv.field_size_limit(sys.maxsize);
    
  #############################################
  def mergeCsvFile(tmp_csv_file1,tmp_csv_file2):
     with open(tmp_csv_file2, 'rb') as csv_read, open(tmp_csv_file1, 'a') as csv_write:
       reader = csv.reader(csv_read);
       headers = reader.next();          
       csv_writer = csv.writer(csv_write);
       for row in reader:  
         csv_writer.writerow(row) ;   
  ################################################       
  
  composite_dataset_folder       ="/data/home/bwang/composite_results_zip";  
  merged_composite_dataset_folder="/data/home/bwang/composite_dataset_merged";
  if not os.path.exists(merged_composite_dataset_folder):
    print '%s folder do not exist, then create it.' % merged_composite_dataset_folder;
    os.makedirs(merged_composite_dataset_folder);
    
  for case_id_zip in os.listdir(composite_dataset_folder)[1:2]:
    print  case_id_zip;
    case_id=case_id_zip.split('.zip')[0];
    print case_id;
    source_zipfile = os.path.join(composite_dataset_folder, case_id_zip);    
    zf = ZipFile(source_zipfile, 'r')
    zf.extractall(merged_composite_dataset_folder)
    zf.close()  
         
    #dest_zipfile = os.path.join(merged_composite_dataset_folder, case_id_zip);
    #if not os.path.isfile(dest_zipfile):
    #  shutil.copy2(source_zipfile,dest_zipfile) ; 
    #else:  
      
    continue;  
          
    print "=== copy all json and csv files to target folders ===";
    composite_dataset_copy_folder = os.path.join(merged_composite_dataset_folder, case_id); 
    if not os.path.exists(composite_dataset_copy_folder):
      print '%s folder do not exist, then create it.' % composite_dataset_copy_folder;
      os.makedirs(composite_dataset_copy_folder);
      
    if os.path.isdir(composite_dataset_copy_folder) and len(os.listdir(composite_dataset_copy_folder)) > 0: 
      print " all csv and json files of this image have been copied from data node."; 
    else:          
      prefix_folder = os.path.join(composite_dataset_folder, case_id);
      for prefix in os.listdir(prefix_folder):
        print case_id,prefix;
        details_folder = os.path.join(prefix_folder, prefix);
      
        json_filename_list = [f for f in os.listdir(details_folder) if f.endswith('.json')] ;
        for json_filename in json_filename_list:   
          json_source_file = os.path.join(details_folder, json_filename);       
          json_dest_file = os.path.join(composite_dataset_copy_folder, json_filename);
          if not os.path.isfile(json_dest_file):
            shutil.copy2(json_source_file,json_dest_file) ;  
             
        csv_filename_list = [f for f in os.listdir(details_folder) if f.endswith('.csv')] ;      
        for csv_filename in csv_filename_list:   
          csv_source_file = os.path.join(details_folder, csv_filename);       
          csv_dest_file = os.path.join(composite_dataset_copy_folder, csv_filename);
          if not os.path.isfile(csv_dest_file):
            shutil.copy2(csv_source_file,csv_dest_file) ;       

    print "=== merge in the new folder and revove duplicate json and csv file  ===";    
    json_filename_list = [f for f in os.listdir(composite_dataset_copy_folder) if f.endswith('.json')] ;
    file_count=len(json_filename_list);
    for index1,json_filename1 in enumerate(json_filename_list[0:file_count]):
      filename1="_x"+json_filename1.split('_x')[1];      
      for index2,json_filename2 in enumerate(json_filename_list[index1+1:]):
        filename2="_x"+json_filename2.split('_x')[1];        
        if(filename1==filename2):#find duplicate json file with same tile info                   
          tmp_json_file = os.path.join(composite_dataset_copy_folder, json_filename2); 
          if os.path.isfile(tmp_json_file):
            os.remove(tmp_json_file);
            print "remove file " + str(json_filename2); 
           
    csv_filename_list = [f for f in os.listdir(composite_dataset_copy_folder) if f.endswith('.csv')] ;
    file_count2=len(csv_filename_list);
    #print file_count2;
    for index1,csv_filename1 in enumerate(csv_filename_list[0:file_count2]):
      #print index1,csv_filename1;
      #if (csv_filename1=="tmp_file_547.csv"):
      #  continue;
      filename1="_x"+csv_filename1.split('_x')[1];      
      for index2,csv_filename2 in enumerate(csv_filename_list[index1+1:]):
        #if (csv_filename2=="tmp_file_1357.csv"):
        #  continue;
        filename2="_x"+csv_filename2.split('_x')[1];        
        if(filename1==filename2):#find duplicate csv file with same tile info                    
          tmp_csv_file1 = os.path.join(composite_dataset_copy_folder, csv_filename1);
          tmp_csv_file2 = os.path.join(composite_dataset_copy_folder, csv_filename2); 
          if os.path.isfile(tmp_csv_file1) and os.path.isfile(tmp_csv_file2):
            mergeCsvFile(tmp_csv_file1,tmp_csv_file2);
            print "merge file " +str(csv_filename1) + " and file " + str(csv_filename2)
          if os.path.isfile(tmp_csv_file2):  
            os.remove(tmp_csv_file2);
            print "remove file " + str(csv_filename2);  
        
    json_filename_list = [f for f in os.listdir(composite_dataset_copy_folder) if f.endswith('.json')] ; 
    csv_filename_list = [f for f in os.listdir(composite_dataset_copy_folder) if f.endswith('.csv')] ;
    print case_id,len(json_filename_list), len(csv_filename_list);

    print "=== find same tile info for json and csv file pair,otherwise change csv file name to match jsion file name ===";        
    for json_filename in json_filename_list:  
      tmp_json = os.path.join(composite_dataset_copy_folder, json_filename);
      findMatchCsv=False;
      with open(tmp_json) as f:
        datajson = json.load(f);        
        tile_x = datajson['tile_minx'];
        tile_y = datajson['tile_miny'];
        tmp_string="_x"+str(tile_x)+"_y" + str(tile_y)+ "-features.csv";                
        for csv_file in csv_filename_list:   
          if csv_file.find(tmp_string) <> -1:#find it!
            findMatchCsv=True;
            new_csv_name=json_filename.replace('-algmeta.json','-features.csv');            
            old_csv_file=os.path.join(composite_dataset_copy_folder, csv_file);
            new_csv_file=os.path.join(composite_dataset_copy_folder, new_csv_name);
            if (csv_file<>new_csv_name):# rename it
              print "chane csv file name.", csv_file,new_csv_name;
              shutil.move(old_csv_file,new_csv_file);           
            break;            
        if not findMatchCsv:
          print "can not find same tile info for json and csv file pair" ,case_id, json_filename; 
    
    json_filename_list = [f for f in os.listdir(composite_dataset_copy_folder) if f.endswith('.json')] ; 
    csv_filename_list = [f for f in os.listdir(composite_dataset_copy_folder) if f.endswith('.csv')] ;
    print case_id,len(json_filename_list), len(csv_filename_list);  
    print "///////////////////////////////////////////"              
  exit();
