from pymongo import MongoClient
from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import affine_transform
from shapely import ops
from bson import json_util 
from matplotlib.path import Path
from skimage import color
from skimage import io
import numpy as np
import time
import pprint
import json 
import csv
import sys
import os
import shutil
import subprocess
import pipes
import shlex
import math
from skimage.color import separate_stains,hed_from_rgb
from skimage import data
import openslide
from PIL import Image
    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_patient_level_dataset.py config.json";
    exit();  
  
  start_time = time.time(); 
  csv.field_size_limit(sys.maxsize);  
   
  remote_folder="nfs001:/data/shared/tcga_analysis/seer_data/results";  
  remote_image_folder="nfs001:/data/shared/tcga_analysis/seer_data/images";  
  my_home="/home/bwang/patient_level";
  local_folder = os.path.join(my_home, 'results');  
  local_image_folder = os.path.join(my_home, 'img'); 
  
  print " --- read config.json file ---" ;
  config_json_file = sys.argv[-1];  
  with open(config_json_file) as json_data:
    d = json.load(json_data);        
    image_list_file = d['image_list'];      
    if not os.path.isfile(image_list_file):
      print "image list_file is not available."
      exit();   
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print image_list_file,patch_size,db_host,db_port,db_name1,db_name2;
  #exit();
  
  print '--- read image_user_list file ---- ';  
  index=0;
  image_list=[];  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list: 
      tmp_array=[[],[]]
      print each_row[0];
      tmp_array[0]=each_row[0];   
      tmp_array[1]=each_row[1];           
      image_list.append(tmp_array);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
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
  
  image_width=0;
  image_height=0;  
  x0=0.0;
  y0=0.0
  tolence=0.05;
  patch_x_num=0; 
  patch_y_num=0;
  
  x, y = np.meshgrid(np.arange(patch_size), np.arange(patch_size)) # make a canvas with coordinates
  x, y = x.flatten(), y.flatten();
  points = np.vstack((x,y)).T ;
  
  #######################################
  def findImagePath(case_id):
    image_path="";  
    input_file="image_path"
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
  
  #############################################
  def findTumor_NonTumorRegions(case_id,user):
    execution_id=user+"_Tumor_Region";
    execution_id2=user+"_Non_Tumor_Region";
    humanMarkupList=[];
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id},
                                 {"geometry":1,"_id":0}):
      humarkup_polygon_tmp=humarkup["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i2) for i2 in humarkup_polygon_tmp];
      tmp_polygon2 = Polygon(tmp_polygon);
      humarkup_polygon = tmp_polygon2.buffer(0);
      humarkup_polygon_bound= humarkup_polygon.bounds;
      humanMarkupList.append(humarkup_polygon);              
    
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id2},
                                  {"geometry":1,"_id":0}):
      humarkup_polygon_tmp=humarkup["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i2) for i2 in humarkup_polygon_tmp];
      tmp_polygon2 = Polygon(tmp_polygon);
      humarkup_polygon = tmp_polygon2.buffer(0);
      humarkup_polygon_bound= humarkup_polygon.bounds;
      humanMarkupList.append(humarkup_polygon);
    return  humanMarkupList;     
  ################################################
  
  ###############################################
  def getCompositeDatasetExecutionID(case_id):
    execution_id="";
    for record in metadata2.find({"image.case_id":case_id,                 
				                          "provenance.analysis_execution_id":{'$regex' : 'composite_dataset', '$options' : 'i'}}).limit(1): 
      execution_id=record["provenance"]["analysis_execution_id"];
      break;
    return execution_id;    
  #################################################  
  
  print '--- process image_list  ---- ';   
  for item in image_list:  
    case_id=item[0];
    user=item[1];
    execution_id=user+"_Tumor_Region";
    execution_id2=user+"_Non_Tumor_Region";
    print case_id,user,execution_id,execution_id2;
    #exit();
    #download image svs file to local folder
    image_file_name=case_id+".svs";
    image_file = os.path.join(local_image_folder, image_file_name);         
    if not os.path.isfile(image_file):
      print "image svs file is not available, then download it to local folder.";
      img_path=findImagePath(case_id);
      full_image_file = os.path.join(remote_image_folder, img_path);      
      subprocess.call(['scp', full_image_file,local_image_folder]);   
    #exit();   
    image_file = os.path.join(local_image_folder, image_file_name);
    print image_file;
    try:
      img = openslide.OpenSlide(image_file);
      print img.detect_format(image_file);
    except Exception as e: 
      print(e);
      continue;  
    print img.level_count;
    print img.level_dimensions;
    print img.level_downsamples;
    print "img.dimensions";
    print img.dimensions;
    print img.properties;  
    image_width =img.dimensions[0];
    image_height =img.dimensions[1];
    print "image_width,image_height";
    print image_width,image_height;
    patch_x_num=math.ceil(image_width/patch_size) ;
    patch_y_num=math.ceil(image_height/patch_size) ;  
    patch_x_num =int(patch_x_num);
    patch_y_num =int(patch_y_num);  
    print "-- case_id,image_width,image_height,patch_size, patch_x_num, patch_y_num --";     
    print case_id,image_width,image_height,patch_size, patch_x_num, patch_y_num;
    humanMarkupList=findTumor_NonTumorRegions(case_id,user); 
    print "humanMarkupList----";
    print humanMarkupList;
    print len(humanMarkupList);
    if(len(humanMarkupList) ==0):
      print "No tumor or non tumor regions has been marked in this image by user %s." % user;
      continue;
    #exit();  
    comp_execution_id=getCompositeDatasetExecutionID(case_id);   
    print "comp_execution_id";
    print comp_execution_id; 
    #exit();       
    for i in range(0,patch_x_num):
      for j in  range (0,patch_y_num): 
        #if(i==0 and j==0):
            #print "i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std"; 
        patchHumanMarkupRelation="";  
        patch_humanmarkup_intersect_polygon = Polygon([(0, 0), (1, 1), (1, 0)]);
        patch_min_x_pixel=i*patch_size;
        patch_min_y_pixel=j*patch_size;     
        x10=(i*float(patch_size))/float(image_width);
        y10=(j*float(patch_size))/float(image_height);
        x20=((i+1)*float(patch_size))/float(image_width);
        y20=((j+1)*float(patch_size))/float(image_height);
        #print i,j,patch_size,image_width,image_height,x10,y10,x20,y20;
        patch_polygon1=[[x10,y10],[x20,y10],[x20,y20],[x10,y20],[x10,y10]];
        tmp_poly=[tuple(i1) for i1 in patch_polygon1];
        tmp_polygon = Polygon(tmp_poly);
        patch_polygon = tmp_polygon.buffer(0);
        patch_polygon_bound= patch_polygon.bounds;
        patch_polygon_area=patch_polygon.area;
        
        for humanMarkup in humanMarkupList:
          if (patch_polygon.within(humanMarkup)):
            #print "-- within --" ;
            patchHumanMarkupRelation="within";
            break;
          elif (patch_polygon.intersects(humanMarkup)):
            #print "-- intersects --";  
            patchHumanMarkupRelation="intersect";  
            patch_humanmarkup_intersect_polygon=humanMarkup;
            break;
          else: 
            #print "-- disjoin --"; 
            patchHumanMarkupRelation="disjoin";
        #print  "patchHumanMarkupRelation";
        #print  patchHumanMarkupRelation;
        if(patchHumanMarkupRelation=="disjoin"):          
            print i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,"n/a","n/a","n/a","n/a";
            continue;        
        try:
          patch_img= img.read_region((patch_min_x_pixel, patch_min_y_pixel), 0, (patch_size, patch_size));
        except openslide.OpenSlideError as detail:
          print 'Handling run-time error:', detail  
          continue;
        except Exception as e: 
          print(e);
          continue;  
        
        grayscale_img = patch_img.convert('L');
        rgb_img = patch_img.convert('RGB');        
        grayscale_img_matrix=np.array(grayscale_img);         
        grayscale_patch_mean=np.mean(grayscale_img_matrix);
        grayscale_patch_std=np.std(grayscale_img_matrix);          
        rgb_img_matrix=np.array(rgb_img);        
        hed_title_img = separate_stains(rgb_img_matrix, hed_from_rgb);               
        Hematoxylin_img_matrix = [[0 for x in range(patch_size)] for y in range(patch_size)] 
        for index1,row in enumerate(hed_title_img):
          for index2,pixel in enumerate(row):
            Hematoxylin_img_matrix[index1][index2]=pixel[0];
        Hematoxylin_patch_mean=np.mean(Hematoxylin_img_matrix);
        Hematoxylin_patch_std=np.std(Hematoxylin_img_matrix);
        
        x1_new=x10-(x10*tolence);
        y1_new=y10-(y10*tolence);
        x2_new=x20+(x20*tolence);
        y2_new=y20+(y20*tolence);       
        nucleus_area=0.0;
        segment_img=[];
        segment_img_hematoxylin=[]; 
        
        ##################################
        def getMatrixValue(poly_in):
         path = Path(poly_in) # make a polygon
         grid = path.contains_points(points);
         mask = grid.reshape(patch_size,patch_size) # now you have a mask with points inside a polygon   
         for index1,row in enumerate(mask):
           for index2,pixel in enumerate(row):
             if (pixel):#this pixel is inside of segmented unclei polygon                     
               segment_img.append(grayscale_img_matrix[index1][index2]);
               segment_img_hematoxylin.append(Hematoxylin_img_matrix[index1][index2]);   
        ##################################################  
         
        record_count =objects2.find({"provenance.image.case_id":case_id,
                                    "provenance.analysis.execution_id":comp_execution_id,                                                                                         
                                    "x" : { '$gte':x1_new, '$lte':x2_new},
                                    "y" : { '$gte':y1_new, '$lte':y2_new} }).count();           
        if (record_count>0):
          #print " find segmented unclei %d." %  record_count;   
          #print patchHumanMarkupRelation;                                                
          for nuclues_polygon in objects2.find({"provenance.image.case_id":case_id,
                                               "provenance.analysis.execution_id":comp_execution_id,                                                                                                   
                                               "x" : { '$gte':x1_new, '$lte':x2_new},
                                               "y" : { '$gte':y1_new, '$lte':y2_new} },{"geometry":1,"_id":0}):
            polygon=nuclues_polygon["geometry"]["coordinates"][0];             
            tmp_poly2=[tuple(i2) for i2 in polygon];
            computer_polygon2 = Polygon(tmp_poly2);
            computer_polygon = computer_polygon2.buffer(0);
            #computer_polygon_bound= computer_polygon.bounds;
            polygon_area= computer_polygon.area;                          
            special_case2="";            
            if (patchHumanMarkupRelation=="intersect"):              
              if(computer_polygon.within(patch_humanmarkup_intersect_polygon)):                
                special_case2="within";
              elif(computer_polygon.intersects(patch_humanmarkup_intersect_polygon)):               
                special_case2="intersects";
              else:                
                special_case2="disjoin";                           
              if (special_case2=="disjoin"):
                continue;#skip this one and move to another computer polygon              
                       
            if (special_case2=="within" and computer_polygon.within(patch_polygon)):#within
              #print "-- within --"  
              nucleus_area=nucleus_area+polygon_area;  
              new_polygon =[];            
              for ii in range (0,len(polygon)):   
                x0=polygon[ii][0];
                y0=polygon[ii][1];                 
                x01=(x0*image_width)- patch_min_x_pixel;
                y01=(y0*image_height)- patch_min_y_pixel;
                x01=int(round(x01)); 
                y01=int(round(y01));                
                point=[x01,y01];
                new_polygon.append(point); 
              if (len(new_polygon) >0):   
                getMatrixValue(new_polygon);                 
            elif (special_case2=="within" and computer_polygon.intersects(patch_polygon)):#intersects                  
              tmp_intersect=computer_polygon.intersection(patch_polygon);
              if tmp_intersect.is_empty:
                continue;
              tmp_area=tmp_intersect.area;
              nucleus_area=nucleus_area+tmp_area;              
              matrix2d = (image_width, 0, 0, image_height, -patch_min_x_pixel, -patch_min_y_pixel)
              polygon_intersect = affine_transform(tmp_intersect, matrix2d);              
              if polygon_intersect.geom_type == 'MultiPolygon':                                 
                for p in polygon_intersect:
                  tmp_polygon111=[];
                  polygon_intersect_points =list(zip(*p.exterior.coords.xy));
                  for jj in range (0,len(polygon_intersect_points)):   
                    x0=polygon_intersect_points[jj][0];
                    y0=polygon_intersect_points[jj][1];                     
                    x01=int(round(x0)); 
                    y01=int(round(y0));                    
                    tmp_point=[x01,y01];
                    tmp_polygon111.append(tmp_point);
                  if (len(tmp_polygon111) >0):   
                    getMatrixValue(tmp_polygon111);                                                    
              elif polygon_intersect.geom_type == 'Polygon':                
                tmp_polygon222=[];
                polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                            
                for jj in range (0,len(polygon_intersect_points)):   
                  x0=polygon_intersect_points[jj][0];
                  y0=polygon_intersect_points[jj][1];                  
                  x01=int(round(x0)); 
                  y01=int(round(y0));                  
                  tmp_point=[x01,y01];
                  tmp_polygon222.append(tmp_point);                   
                if (len(tmp_polygon222) >0):   
                  getMatrixValue(tmp_polygon222);
              else:               
               print "patch indexes %d , %d Shape is not a polygon!!!" %(i,j); 
               print polygon_intersect;   
            elif (special_case2=="intersects" and computer_polygon.within(patch_polygon)):#intersects and within
              tmp_intersect=computer_polygon.intersection(patch_humanmarkup_intersect_polygon); 
              if tmp_intersect.is_empty:
                continue; 
              tmp_area=tmp_intersect.area;
              nucleus_area=nucleus_area+tmp_area;              
              matrix2d = (image_width, 0, 0, image_height, -patch_min_x_pixel, -patch_min_y_pixel)
              polygon_intersect = affine_transform(tmp_intersect, matrix2d);              
              if polygon_intersect.geom_type == 'MultiPolygon':                                 
                for p in polygon_intersect:
                  tmp_polygon111=[];
                  polygon_intersect_points =list(zip(*p.exterior.coords.xy));
                  for jj in range (0,len(polygon_intersect_points)):   
                    x0=polygon_intersect_points[jj][0];
                    y0=polygon_intersect_points[jj][1];                     
                    x01=int(round(x0)); 
                    y01=int(round(y0));                    
                    tmp_point=[x01,y01];
                    tmp_polygon111.append(tmp_point);
                  if (len(tmp_polygon111) >0):   
                    getMatrixValue(tmp_polygon111);                                                    
              elif polygon_intersect.geom_type == 'Polygon':                
                tmp_polygon222=[];
                polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                            
                for jj in range (0,len(polygon_intersect_points)):   
                  x0=polygon_intersect_points[jj][0];
                  y0=polygon_intersect_points[jj][1];                  
                  x01=int(round(x0)); 
                  y01=int(round(y0));                  
                  tmp_point=[x01,y01];
                  tmp_polygon222.append(tmp_point);                   
                if (len(tmp_polygon222) >0):   
                  getMatrixValue(tmp_polygon222);
              else:               
               print "patch indexes %d , %d Shape is not a polygon!!!" %(i,j); 
               print polygon_intersect;   
            elif (special_case2=="intersects" and computer_polygon.intersects(patch_polygon)):#intersects and intersects
              tmp_intersect1=computer_polygon.intersection(patch_polygon);
              if tmp_intersect1.is_empty:
                continue;
              tmp_intersect=tmp_intersect1.intersection(patch_humanmarkup_intersect_polygon); 
              if tmp_intersect.is_empty:
                continue;              
              tmp_area=tmp_intersect.area;
              nucleus_area=nucleus_area+tmp_area;              
              matrix2d = (image_width, 0, 0, image_height, -patch_min_x_pixel, -patch_min_y_pixel)
              polygon_intersect = affine_transform(tmp_intersect, matrix2d);              
              if polygon_intersect.geom_type == 'MultiPolygon':                                 
                for p in polygon_intersect:
                  tmp_polygon111=[];
                  polygon_intersect_points =list(zip(*p.exterior.coords.xy));
                  for jj in range (0,len(polygon_intersect_points)):   
                    x0=polygon_intersect_points[jj][0];
                    y0=polygon_intersect_points[jj][1];                     
                    x01=int(round(x0)); 
                    y01=int(round(y0));                    
                    tmp_point=[x01,y01];
                    tmp_polygon111.append(tmp_point);
                  if (len(tmp_polygon111) >0):   
                    getMatrixValue(tmp_polygon111);                                                    
              elif polygon_intersect.geom_type == 'Polygon':                
                tmp_polygon222=[];
                polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                            
                for jj in range (0,len(polygon_intersect_points)):   
                  x0=polygon_intersect_points[jj][0];
                  y0=polygon_intersect_points[jj][1];                  
                  x01=int(round(x0)); 
                  y01=int(round(y0));                  
                  tmp_point=[x01,y01];
                  tmp_polygon222.append(tmp_point);                   
                if (len(tmp_polygon222) >0):   
                  getMatrixValue(tmp_polygon222);
              else:               
               print "patch indexes %d , %d Shape is not a polygon!!!" %(i,j);  
               print polygon_intersect;                             
        
        percent_nuclear_material =(nucleus_area/patch_polygon_area)*100;         
        if (len(segment_img)>0):          
          segment_mean_grayscale_intensity= np.mean(segment_img);
          segment_std_grayscale_intensity= np.std(segment_img); 
          segment_mean_hematoxylin_intensity= np.mean(segment_img_hematoxylin);
          segment_std_hematoxylin_intensity= np.std(segment_img_hematoxylin);         
        else:
          segment_mean_grayscale_intensity="n/a";
          segment_std_grayscale_intensity="n/a";
          segment_mean_hematoxylin_intensity="n/a";
          segment_std_hematoxylin_intensity="n/a";        
        #print " --- i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity ---";
        print i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity;         
        #print " ---segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity --"; 
        #print segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity; 
             
    img.close();        
  exit();  
 
