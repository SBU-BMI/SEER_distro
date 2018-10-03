import csv
import sys
import os
import shutil
import subprocess
import json
    
    
if __name__ == '__main__':
  if len(sys.argv)<0:
    print "usage:python tile_merge.py";
    exit();   
  
  csv.field_size_limit(sys.maxsize); 
   
  my_home="/home/bwang/patch_level"  
  remote_dataset_folder="nfs004:/data/shared/bwang/composite_dataset";  
   
  local_dataset_folder = os.path.join(my_home, 'dataset');  
  if not os.path.exists(local_dataset_folder):
    print '%s folder do not exist, then create it.' % local_dataset_folder;
    os.makedirs(local_dataset_folder); 
  
  local_dataset_folder_new = os.path.join(my_home, 'composite_merged');  
  if not os.path.exists(local_dataset_folder_new):
    print '%s folder do not exist, then create it.' % local_dataset_folder_new;
    os.makedirs(local_dataset_folder_new);    
    
  print '--- read case_id_list file ---- ';  
  index=0;
  image_list=[];  
  image_list_file="case_id_list.txt"
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:
      case_id=each_row[0];                 
      image_list.append(case_id);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  #print image_list;
  #exit(); 
  
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
  
  #############################################
  def mergeCsvFile(tmp_csv_file1,tmp_csv_file2):
     with open(tmp_csv_file2, 'rb') as csv_read, open(tmp_csv_file1, 'a') as csv_write:
       reader = csv.reader(csv_read);
       headers = reader.next();          
       csv_writer = csv.writer(csv_write);
       for row in reader:  
         csv_writer.writerow(row) ;   
  ################################################
  
  
  '''  
  print '--- process image_list  ---- ';   
  for case_id  in image_list[10:]: 
           
    prefix_list=findPrefixList(case_id);
    if(len(prefix_list))<1:
      print "can NOT find prefix of this image!"
      exit();    
      
    #create local folder
    local_img_folder = os.path.join(local_dataset_folder, case_id);   
    if not os.path.exists(local_img_folder):
      print '%s folder do not exist, then create it.' % local_img_folder;
      os.makedirs(local_img_folder);  
         
    #create local folder_new
    local_img_folder_new = os.path.join(local_dataset_folder_new, case_id);   
    if not os.path.exists(local_img_folder_new):
      print '%s folder do not exist, then create it.' % local_img_folder_new;
      os.makedirs(local_img_folder_new);  
         
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
    
    if os.path.isdir(local_img_folder_new) and len(os.listdir(local_img_folder_new)) > 0: 
      print " all csv and json files of this image have been copied to composiye_merged folder."; 
      continue;
        
    total_jsonfile_count=0;
    total_csvfile_count=0;  
    total_jsonfile_count2=0;
    total_csvfile_count2=0;       
    for prefix in prefix_list:
      detail_local_folder  = os.path.join(local_img_folder, prefix);      
      if os.path.isdir(detail_local_folder) and len(os.listdir(detail_local_folder)) > 0:                            
        json_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.json')] ;    
        print "json_filename",case_id,prefix,len(json_filename_list) ; 
        total_jsonfile_count2 =   total_jsonfile_count2 +  len(json_filename_list);                      
        for json_filename in json_filename_list:   
           json_source_file = os.path.join(detail_local_folder, json_filename);       
           json_dest_file = os.path.join(local_img_folder_new, json_filename);           
           if not os.path.isfile(json_dest_file):
             shutil.copy2(json_source_file,json_dest_file) ;  
             total_jsonfile_count+=1;
           else:
             print "json file " + str(json_filename) + " already exist!";  
                    
        csv_filename_list = [f for f in os.listdir(detail_local_folder) if f.endswith('.csv')] ; 
        print "csv_filename",case_id,prefix,len(csv_filename_list) ;
        total_csvfile_count2 =  total_csvfile_count2 + len(csv_filename_list);
        for csv_filename in csv_filename_list:   
           csv_source_file = os.path.join(detail_local_folder, csv_filename);       
           csv_dest_file = os.path.join(local_img_folder_new, csv_filename);
           if not os.path.isfile(csv_dest_file):
             shutil.copy2(csv_source_file,csv_dest_file) ;
             total_csvfile_count+=1;
           else:
             print "csv file " + str(csv_filename) + " already exist!";                                       
             with open(csv_source_file, 'rb') as csv_read, open(csv_dest_file, 'a') as csv_write:
               reader = csv.reader(csv_read);
               headers = reader.next();          
               csv_writer = csv.writer(csv_write);
               for row in reader:  
                 csv_writer.writerow(row) ;  
                  
    total_count=total_jsonfile_count+total_csvfile_count;
    total_count2=total_jsonfile_count2+total_csvfile_count2;
    print case_id, total_jsonfile_count,total_csvfile_count ,total_count;
    print case_id, total_jsonfile_count2,total_csvfile_count2 ,total_count2;
    total_file_count=len(os.listdir(local_img_folder_new)) ;
    print case_id,total_file_count; 
    print  "================================";
    shutil.rmtree(local_img_folder)    
  '''
  
  '''  
  print "===find duplicate tile and merge/remove them ===";
  for case_id in os.listdir(local_dataset_folder_new)[1:]:
    print  case_id;
    #duplicate_json_file_list0=[];
    #duplicate_csv_file_list0=[];    
    local_img_folder_new = os.path.join(local_dataset_folder_new, case_id);
    json_filename_list = [f for f in os.listdir(local_img_folder_new) if f.endswith('.json')] ;
    file_count=len(json_filename_list);
    for index1,json_filename1 in enumerate(json_filename_list[0:file_count]):
      filename1="_x"+json_filename1.split('_x')[1];
      #print index1,filename1;
      for index2,json_filename2 in enumerate(json_filename_list[index1+1:]):
        filename2="_x"+json_filename2.split('_x')[1];
        #print index2,filename2
        if(filename1==filename2):
          #print "find same file  " + str(filename2);
          #print json_filename1,json_filename2;
          #duplicate_json_file_list0.append(json_filename2);
          tmp_json_file = os.path.join(local_img_folder_new, json_filename2); 
          if os.path.isfile(tmp_json_file):
            os.remove(tmp_json_file);
            print "remove file " + str(json_filename2);                               
          #print "----------------------";   
    csv_filename_list = [f for f in os.listdir(local_img_folder_new) if f.endswith('.csv')] ;
    file_count2=len(csv_filename_list);
    for index1,csv_filename1 in enumerate(csv_filename_list[0:file_count2]):
      filename1="_x"+csv_filename1.split('_x')[1];
      #print index1,filename1;
      for index2,csv_filename2 in enumerate(csv_filename_list[index1+1:]):
        filename2="_x"+csv_filename2.split('_x')[1];
        #print index2,filename2
        if(filename1==filename2):
          #print "find same file  " + str(filename2);
          #print csv_filename1,csv_filename2;
          #duplicate_csv_file_list0.append(csv_filename2);
          tmp_csv_file1 = os.path.join(local_img_folder_new, csv_filename1);
          tmp_csv_file2 = os.path.join(local_img_folder_new, csv_filename2); 
          if os.path.isfile(tmp_csv_file1) and os.path.isfile(tmp_csv_file2):
            mergeCsvFile(tmp_csv_file1,tmp_csv_file2);
            print "merge file " +str(csv_filename1) + " and file " + str(csv_filename2)
          if os.path.isfile(tmp_csv_file2):  
            os.remove(tmp_csv_file2);
            print "remove file " + str(csv_filename2);                               
          #print "----------------------";
    print "===========================";      
    
    #tmp_set = set(map(tuple,duplicate_json_file_list0))
    #duplicate_json_file_list = map(list,tmp_set) 
    #tmp_set = set(map(tuple,duplicate_csv_file_list0))
    #duplicate_csv_file_list = map(list,tmp_set) ;
    #print duplicate_json_file_list0;
    #print duplicate_csv_file_list0;    
    #exit();    
  '''
      
  '''
  print "===find duplicate tile and merge/remove them ===";
  for case_id in os.listdir(local_dataset_folder_new):
    #print  case_id;
    local_img_folder_new = os.path.join(local_dataset_folder_new, case_id);
    json_filename_list = [f for f in os.listdir(local_img_folder_new) if f.endswith('.json')] ;
    csv_filename_list = [f for f in os.listdir(local_img_folder_new) if f.endswith('.csv')] ;
    file_count=len(json_filename_list); 
    file_count2=len(csv_filename_list);
    #print  case_id,file_count,file_count2; 
    #if (file_count<>file_count2):
    #  print "error???"  
    for json_filename in json_filename_list:  
      filename1="_x"+json_filename.split('_x')[1];  
      filename2=filename1.split('-algmeta.json')[0];     
      filename=filename2 + "-features.csv";
      #print  case_id, json_filename,filename1,filename2,filename;
      findCSVpair=False;
      for csv_json_file in csv_filename_list:   
        if csv_json_file.endswith("features.csv") and csv_json_file.find(filename) <> -1:#find it!
          findCSVpair=True;
          break;
      if not findCSVpair:
        print "Not find csv pair"; 
        print case_id, json_filename,filename1,filename2,filename   
      #exit(); 
  '''      
      
  traget_x=45504;
  traget_y=43240;    
  for case_id in os.listdir(local_dataset_folder_new):
    #print  case_id;
    if case_id <> "17032560":
      continue;
    print  case_id;  
    local_img_folder_new = os.path.join(local_dataset_folder_new, case_id);
    json_filename_list = [f for f in os.listdir(local_img_folder_new) if f.endswith('.json')] ; 
    csv_filename_list = [f for f in os.listdir(local_img_folder_new) if f.endswith('.csv')] ;   
    for json_filename in json_filename_list: 
      tmp_json = os.path.join(local_img_folder_new, json_filename);                
      # Read json file
      with open(tmp_json) as f:
        datajson = json.load(f);        
        tile_x = datajson['tile_minx'];
        tile_y = datajson['tile_miny'];
        tmp_string="_x"+str(tile_x)+"_y" + str(tile_y); 
        tile_width = datajson['tile_width'];
        tile_height = datajson['tile_height'];
        tile_max_x=tile_x+tile_width;
        tile_max_y=tile_y+tile_height;
        if (traget_x>=tile_x and traget_x <= tile_max_x):
          if (traget_y>=tile_y and traget_y <= tile_max_y): 
            print  json_filename;
            for csv_file in csv_filename_list:   
              if csv_file.find(tmp_string) <> -1:#find it!
                print csv_file;
                exit();
        
                        
  exit(); 
