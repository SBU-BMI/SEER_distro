from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.affinity import affine_transform
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
import datetime
import random

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_heatmap.py config.json";
    exit();  
   
  csv.field_size_limit(sys.maxsize);  
   
  remote_image_folder="nfs001:/data/shared/tcga_analysis/seer_data/images";  
  my_home="/home/bwang/patch_level";    
  local_image_folder = os.path.join(my_home, 'img'); 
  
  print " --- read config.json file ---" ;
  config_json_file = sys.argv[-1];  
  with open(config_json_file) as json_data:
    d = json.load(json_data);        
    image_list_file = d['image_list'];  
    print image_list_file;    
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
  
  patch_level_features = db2.patch_level_features;  
  patch_level_tumor_based_features = db2.patch_level_tumor_based_features;
  image_width=0;
  image_height=0;    
  tolerance=0.05;
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
  
  
  ###############################################
  def getCompositeDatasetExecutionID(case_id):
    execution_id="";
    for record in metadata2.find({"image.case_id":case_id,                 
				                          "provenance.analysis_execution_id":{'$regex' : 'composite_dataset', '$options' : 'i'}}).limit(1): 
      execution_id=record["provenance"]["analysis_execution_id"];
      break;
    return execution_id;    
  #################################################     
  
  #########################################################
  def saveFeatures2Mongo(case_id,image_width,image_height,user,patch_width_index,patch_height_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,grayscale_segment_mean,grayscale_segment_std,Hematoxylin_segment_mean,Hematoxylin_segment_std,grayscale_patch_10th_percentile,grayscale_patch_25th_percentile,grayscale_patch_50th_percentile,grayscale_patch_75th_percentile,grayscale_patch_90th_percentile,Hematoxylin_patch_10th_percentile,Hematoxylin_patch_25th_percentile,Hematoxylin_patch_50th_percentile,Hematoxylin_patch_75th_percentile,Hematoxylin_patch_90th_percentile,segment_10th_percentile_grayscale_intensity,segment_25th_percentile_grayscale_intensity,segment_50th_percentile_grayscale_intensity,segment_75th_percentile_grayscale_intensity,segment_90th_percentile_grayscale_intensity,segment_10th_percentile_hematoxylin_intensity,segment_25th_percentile_hematoxylin_intensity,segment_50th_percentile_hematoxylin_intensity,segment_75th_percentile_hematoxylin_intensity,segment_90th_percentile_hematoxylin_intensity):
    patch_feature_data = collections.OrderedDict();
    patch_feature_data['case_id'] = case_id;
    patch_feature_data['image_width'] = image_width;
    patch_feature_data['image_height'] = image_height;    
    patch_feature_data['user'] = user;
    patch_feature_data['patch_width_index'] = patch_width_index;
    patch_feature_data['patch_height_index'] = patch_height_index;
    patch_feature_data['patch_min_x_pixel'] =patch_min_x_pixel;
    patch_feature_data['patch_min_y_pixel'] = patch_min_y_pixel;
    patch_feature_data['patch_size'] = patch_size;
    patch_feature_data['patch_polygon_area'] = patch_polygon_area;
    patch_feature_data['nucleus_area'] = nucleus_area;
    patch_feature_data['percent_nuclear_material'] = percent_nuclear_material;
    patch_feature_data['grayscale_patch_mean'] = grayscale_patch_mean;
    patch_feature_data['grayscale_patch_std'] = grayscale_patch_std;
    patch_feature_data['Hematoxylin_patch_mean'] = Hematoxylin_patch_mean;
    patch_feature_data['Hematoxylin_patch_std'] = Hematoxylin_patch_std;
    patch_feature_data['grayscale_segment_mean'] = grayscale_segment_mean;
    patch_feature_data['grayscale_segment_std'] = grayscale_segment_std;
    patch_feature_data['Hematoxylin_segment_mean'] = Hematoxylin_segment_mean;
    patch_feature_data['Hematoxylin_segment_std'] = Hematoxylin_segment_std;    
    patch_feature_data['grayscale_patch_10th_percentile'] = grayscale_patch_10th_percentile;  
    patch_feature_data['grayscale_patch_25th_percentile'] = grayscale_patch_25th_percentile;
    patch_feature_data['grayscale_patch_50th_percentile'] = grayscale_patch_50th_percentile;
    patch_feature_data['grayscale_patch_75th_percentile'] = grayscale_patch_75th_percentile;
    patch_feature_data['grayscale_patch_90th_percentile'] = grayscale_patch_90th_percentile;    
    patch_feature_data['Hematoxylin_patch_10th_percentile'] = Hematoxylin_patch_10th_percentile;  
    patch_feature_data['Hematoxylin_patch_25th_percentile'] = Hematoxylin_patch_25th_percentile;
    patch_feature_data['Hematoxylin_patch_50th_percentile'] = Hematoxylin_patch_50th_percentile;
    patch_feature_data['Hematoxylin_patch_75th_percentile'] = Hematoxylin_patch_75th_percentile;
    patch_feature_data['Hematoxylin_patch_90th_percentile'] = Hematoxylin_patch_90th_percentile;    
    patch_feature_data['segment_10th_percentile_grayscale_intensity'] = segment_10th_percentile_grayscale_intensity;  
    patch_feature_data['segment_25th_percentile_grayscale_intensity'] = segment_25th_percentile_grayscale_intensity;
    patch_feature_data['segment_50th_percentile_grayscale_intensity'] = segment_50th_percentile_grayscale_intensity;
    patch_feature_data['segment_75th_percentile_grayscale_intensity'] = segment_75th_percentile_grayscale_intensity;
    patch_feature_data['segment_90th_percentile_grayscale_intensity'] = segment_90th_percentile_grayscale_intensity;    
    patch_feature_data['segment_10th_percentile_hematoxylin_intensity'] = segment_10th_percentile_hematoxylin_intensity;  
    patch_feature_data['segment_25th_percentile_hematoxylin_intensity'] = segment_25th_percentile_hematoxylin_intensity;
    patch_feature_data['segment_50th_percentile_hematoxylin_intensity'] = segment_50th_percentile_hematoxylin_intensity;
    patch_feature_data['segment_75th_percentile_hematoxylin_intensity'] = segment_75th_percentile_hematoxylin_intensity;
    patch_feature_data['segment_90th_percentile_hematoxylin_intensity'] = segment_90th_percentile_hematoxylin_intensity;             
    patch_level_features.insert_one(patch_feature_data);         
  ######################################################################  
  
  ###################################################################### 
  def save2Meta(case_id,tumorFlag):     
    subject_id = case_id;  
    if(subject_id[0:4] == "TCGA"):
      subject_id = case_id.substr(0,12);     
    print case_id,subject_id;
       
    #dict_meta = {}
    dict_meta = collections.OrderedDict();
    # Form dictionary for json
    dict_img = {}
    dict_img['case_id'] = case_id 
    dict_img['subject_id'] = subject_id
    
    if(tumorFlag=="tumor"):
      title="heatmap_percent_nuclear_material_tumor";
      analysis_execution_id ="percent_nuclear_material_tumor";
    else:  
      title="heatmap_percent_nuclear_material_non_tumor";
      analysis_execution_id ="percent_nuclear_material_non_tumor";    
     
    dict_meta['color'] = 'yellow'
    dict_meta['title'] = title
    dict_meta['image'] = dict_img

    dict_meta_provenance = {}
    dict_meta_provenance['analysis_execution_id'] = analysis_execution_id;
    dict_meta_provenance['study_id'] = 'SEER'
    dict_meta_provenance['type'] = 'computer'    
    dict_meta['provenance'] = dict_meta_provenance

    dict_meta['submit_date'] = datetime.datetime.now()
    dict_meta['randval'] = random.uniform(0,1)
    print dict_meta;
    metadata.insert_one(dict_meta);
  ######################################################################
 
    
  print '--- process image_list  ---- ';   
  for item in image_list:  
    case_id=item[0];
    user=item[1];
    #save2Meta(case_id,"tumor");
    record_count=patch_level_tumor_based_features.find({"case_id":case_id}).count();
    print record_count ;   
    exit();    
    
    
    execution_id=user+"_Tumor_Region";
    execution_id2=user+"_Non_Tumor_Region";
    print case_id,user,execution_id,execution_id2;   
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
    except Exception as e: 
      print(e);
      exit(); 
    #print img.detect_format(image_file); 
    #print img.level_count;
    #print img.level_dimensions;
    #print img.level_downsamples;
    #print "img.dimensions";
    #print img.dimensions;
    #print img.properties;  
    image_width =img.dimensions[0];
    image_height =img.dimensions[1];    
    patch_x_num=math.ceil(image_width/patch_size) ;
    patch_y_num=math.ceil(image_height/patch_size) ;  
    patch_x_num =int(patch_x_num);
    patch_y_num =int(patch_y_num);        
    comp_execution_id=getCompositeDatasetExecutionID(case_id);    
    #process patach by patch       
    for i in range(0,patch_x_num):
      for j in  range (0,patch_y_num):         
        patch_min_x_pixel=i*patch_size;
        patch_min_y_pixel=j*patch_size;  
        patch_width_unit=float(patch_size)/float(image_width); 
        patch_height_unit=float(patch_size)/float(image_height);  
        x10=float(i*float(patch_size))/float(image_width);
        y10=float(j*float(patch_size))/float(image_height);
        x20=float((i+1)*float(patch_size))/float(image_width);
        y20=float((j+1)*float(patch_size))/float(image_height);
        #print i,j,patch_size,image_width,image_height,x10,y10,x20,y20;
        patch_polygon1=[[x10,y10],[x20,y10],[x20,y20],[x10,y20],[x10,y10]];
        tmp_poly=[tuple(i1) for i1 in patch_polygon1];
        tmp_polygon = Polygon(tmp_poly);
        patch_polygon = tmp_polygon.buffer(0);
        patch_polygon_bound= patch_polygon.bounds;
        patch_polygon_area=patch_polygon.area;
                      
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
        rgb_img_matrix=np.array(rgb_img); 
        #print grayscale_img_matrix,grayscale_img_matrix.shape;
        #print rgb_img_matrix,rgb_img_matrix.shape;  
        #exit();    
        grayscale_patch_mean=np.mean(grayscale_img_matrix);
        grayscale_patch_std=np.std(grayscale_img_matrix);    
        grayscale_patch_10th_percentile=np.percentile(grayscale_img_matrix,10);
        grayscale_patch_25th_percentile=np.percentile(grayscale_img_matrix,25);
        grayscale_patch_50th_percentile=np.percentile(grayscale_img_matrix,50);
        grayscale_patch_75th_percentile=np.percentile(grayscale_img_matrix,75);
        grayscale_patch_90th_percentile=np.percentile(grayscale_img_matrix,90);              
        hed_title_img = separate_stains(rgb_img_matrix, hed_from_rgb);               
        Hematoxylin_img_matrix = [[0 for x in range(patch_size)] for y in range(patch_size)] 
        for index1,row in enumerate(hed_title_img):
          for index2,pixel in enumerate(row):
            Hematoxylin_img_matrix[index1][index2]=pixel[0];
        Hematoxylin_patch_mean=np.mean(Hematoxylin_img_matrix);
        Hematoxylin_patch_std=np.std(Hematoxylin_img_matrix);
        Hematoxylin_patch_10th_percentile=np.percentile(Hematoxylin_img_matrix,10);
        Hematoxylin_patch_25th_percentile=np.percentile(Hematoxylin_img_matrix,25);
        Hematoxylin_patch_50th_percentile=np.percentile(Hematoxylin_img_matrix,50);
        Hematoxylin_patch_75th_percentile=np.percentile(Hematoxylin_img_matrix,75);
        Hematoxylin_patch_90th_percentile=np.percentile(Hematoxylin_img_matrix,90);        
        x1_new=float(x10-(patch_width_unit*tolerance));
        y1_new=float(y10-(patch_height_unit*tolerance));
        x2_new=float(x20+(patch_width_unit*tolerance));
        y2_new=float(y20+(patch_height_unit*tolerance));       
        nucleus_area=0.0;
        segment_img=[];
        segment_img_hematoxylin=[];         
        initial_grid=np.full((patch_size*patch_size), False); 
        findPixelWithinPolygon=False;       
        
        ##################################
        def getMatrixValue(poly_in):          
          tmp_polygon =[];            
          for ii in range (0,len(poly_in)):   
            x0=poly_in[ii][0];
            y0=poly_in[ii][1];                 
            x01=(x0*image_width)- patch_min_x_pixel;
            y01=(y0*image_height)- patch_min_y_pixel;
            x01=int(round(x01)); 
            y01=int(round(y01));                
            point=[x01,y01];
            tmp_polygon.append(point);           
          if (len(tmp_polygon) >0):   
            path = Path(tmp_polygon)            
            grid = path.contains_points(points);
            return True,grid;
          else:
            return False, "";          
        ##################################################         
         
        record_count =objects2.find({"provenance.image.case_id":case_id,
                                    "provenance.analysis.execution_id":comp_execution_id,                                                                                         
                                    "x" : { '$gte':x1_new, '$lte':x2_new},
                                    "y" : { '$gte':y1_new, '$lte':y2_new} }).count();           
        if (record_count>0):  
          #print " find segmented unclei %d." %  record_count;                                                               
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
            
            if (computer_polygon.within(patch_polygon)):#within              
              nucleus_area=nucleus_area+polygon_area;                                         
              has_value,one_polygon_mask=getMatrixValue(polygon); 
              if(has_value):
                initial_grid = initial_grid | one_polygon_mask; 
                findPixelWithinPolygon=True;                                        
            elif (computer_polygon.intersects(patch_polygon)):#intersects                                           
              polygon_intersect=computer_polygon.intersection(patch_polygon);
              if polygon_intersect.is_empty:
                continue;
              tmp_area=polygon_intersect.area;
              nucleus_area=nucleus_area+tmp_area;                            
              if polygon_intersect.geom_type == 'MultiPolygon':                                 
                for p in polygon_intersect:
                  polygon_intersect_points =list(zip(*p.exterior.coords.xy));                                    
                  has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points);  
                  if(has_value):
                    initial_grid = initial_grid | one_polygon_mask; 
                    findPixelWithinPolygon=True;                                                                
              elif polygon_intersect.geom_type == 'Polygon':               
                polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));                                
                has_value,one_polygon_mask=getMatrixValue(polygon_intersect_points);  
                if(has_value):
                  initial_grid = initial_grid | one_polygon_mask; 
                  findPixelWithinPolygon=True;             
              else:               
                print "patch indexes %d , %d Shape is not a polygon!!!" %(i,j); 
                print polygon_intersect;                    
                                                      
        
        if(findPixelWithinPolygon):          
          mask = initial_grid.reshape(patch_size,patch_size);             
          for index1,row in enumerate(mask):
            for index2,pixel in enumerate(row):
              if (pixel):#this pixel is inside of segmented unclei polygon                     
                segment_img.append(grayscale_img_matrix[index1][index2]);
                segment_img_hematoxylin.append(Hematoxylin_img_matrix[index1][index2]);     
               
        percent_nuclear_material =float((nucleus_area/patch_polygon_area)*100);         
        if (len(segment_img)>0):          
          segment_mean_grayscale_intensity= np.mean(segment_img);
          segment_std_grayscale_intensity= np.std(segment_img); 
          segment_10th_percentile_grayscale_intensity=np.percentile(segment_img,10); 
          segment_25th_percentile_grayscale_intensity=np.percentile(segment_img,25);
          segment_50th_percentile_grayscale_intensity=np.percentile(segment_img,50);
          segment_75th_percentile_grayscale_intensity=np.percentile(segment_img,75);
          segment_90th_percentile_grayscale_intensity=np.percentile(segment_img,90);
          segment_mean_hematoxylin_intensity= np.mean(segment_img_hematoxylin);
          segment_std_hematoxylin_intensity= np.std(segment_img_hematoxylin); 
          segment_10th_percentile_hematoxylin_intensity=np.percentile(segment_img_hematoxylin,10); 
          segment_25th_percentile_hematoxylin_intensity=np.percentile(segment_img_hematoxylin,25);
          segment_50th_percentile_hematoxylin_intensity=np.percentile(segment_img_hematoxylin,50);
          segment_75th_percentile_hematoxylin_intensity=np.percentile(segment_img_hematoxylin,75);
          segment_90th_percentile_hematoxylin_intensity=np.percentile(segment_img_hematoxylin,90);                    
        else:
          segment_mean_grayscale_intensity="n/a";
          segment_std_grayscale_intensity="n/a";
          segment_mean_hematoxylin_intensity="n/a";
          segment_std_hematoxylin_intensity="n/a";   
          segment_10th_percentile_grayscale_intensity="n/a";
          segment_25th_percentile_grayscale_intensity="n/a";
          segment_50th_percentile_grayscale_intensity ="n/a"; 
          segment_75th_percentile_grayscale_intensity="n/a"; 
          segment_90th_percentile_grayscale_intensity ="n/a"; 
          segment_10th_percentile_hematoxylin_intensity="n/a"; 
          segment_25th_percentile_hematoxylin_intensity="n/a";
          segment_50th_percentile_hematoxylin_intensity="n/a";
          segment_75th_percentile_hematoxylin_intensity="n/a";
          segment_90th_percentile_hematoxylin_intensity="n/a";
        print case_id,image_width,image_height,user,i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity;         
        saveFeatures2Mongo(case_id,image_width,image_height,user,i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,grayscale_patch_10th_percentile,grayscale_patch_25th_percentile,grayscale_patch_50th_percentile,grayscale_patch_75th_percentile,grayscale_patch_90th_percentile,Hematoxylin_patch_10th_percentile,Hematoxylin_patch_25th_percentile,Hematoxylin_patch_50th_percentile,Hematoxylin_patch_75th_percentile,Hematoxylin_patch_90th_percentile,segment_10th_percentile_grayscale_intensity,segment_25th_percentile_grayscale_intensity,segment_50th_percentile_grayscale_intensity,segment_75th_percentile_grayscale_intensity,segment_90th_percentile_grayscale_intensity,segment_10th_percentile_hematoxylin_intensity,segment_25th_percentile_hematoxylin_intensity,segment_50th_percentile_hematoxylin_intensity,segment_75th_percentile_hematoxylin_intensity,segment_90th_percentile_hematoxylin_intensity);               
    img.close();        
  exit();  
 
