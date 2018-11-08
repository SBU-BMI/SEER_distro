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
import concurrent.futures 
    
    
if __name__ == '__main__':
  if len(sys.argv)<2:
    print "usage:python generate_region_level_features.py case_id user";
    exit();  
  
  csv.field_size_limit(sys.maxsize);  
  max_workers=16;    
  
  case_id= sys.argv[1];
  user= sys.argv[2] ;
  
  image_list=[];  
  tmp_array=[[],[]];
  tmp_array[0]=case_id;   
  tmp_array[1]=user;
  image_list.append(tmp_array);   
  print image_list; 
  #print sys.maxsize; 
  #exit();
   
  remote_image_folder="nfs001:/data/shared/tcga_analysis/seer_data/images";  
  my_home="/home/bwang/patch_level";    
  local_image_folder = os.path.join(my_home, 'img'); 
  if not os.path.exists(local_image_folder):
    print '%s folder do not exist, then create it.' % local_image_folder;
    os.makedirs(local_image_folder); 
        
  print " --- read config.json file ---" ;
  config_json_file_name = "config_175.json";  
  config_json_file = os.path.join(my_home, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;
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
   
  collection_saved= db2.patch_level_features_new;
  
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
    input_file="image_path.txt"
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
    
    #handle only tumor region overlap
    humanMarkupList_tumor=[];
    tmp_tumor_markup_list=[];
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id},
                                 {"geometry":1,"_id":0}):
      tmp_tumor_markup_list.append(humarkup); 
              
    index_intersected=[];                                
    for index1 in range(0, len(tmp_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      tmp_tumor_markup1=tmp_tumor_markup_list[index1];                               
      humarkup_polygon_tmp1=tmp_tumor_markup1["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i1) for i1 in humarkup_polygon_tmp1];
      tmp_polygon1 = Polygon(tmp_polygon);
      humarkup_polygon1 = tmp_polygon1.buffer(0);
      humarkup_polygon_bound1= humarkup_polygon1.bounds;
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_tumor_markup_list)):  
        tmp_tumor_markup2=tmp_tumor_markup_list[index2];                               
        humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
        tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
        tmp_polygon22 = Polygon(tmp_polygon2);
        humarkup_polygon2 = tmp_polygon22.buffer(0);
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
        
    #handle only non tumor region overlap
    humanMarkupList_non_tumor=[];
    tmp_non_tumor_markup_list=[];
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id2},
                                 {"geometry":1,"_id":0}):
      tmp_non_tumor_markup_list.append(humarkup);     
        
    index_intersected=[];                                
    for index1 in range(0, len(tmp_non_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      tmp_tumor_markup1=tmp_non_tumor_markup_list[index1];                               
      humarkup_polygon_tmp1=tmp_tumor_markup1["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i1) for i1 in humarkup_polygon_tmp1];
      tmp_polygon1 = Polygon(tmp_polygon);
      humarkup_polygon1 = tmp_polygon1.buffer(0);
      humarkup_polygon_bound1= humarkup_polygon1.bounds;
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_non_tumor_markup_list)):  
        tmp_tumor_markup2=tmp_non_tumor_markup_list[index2];                               
        humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
        tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
        tmp_polygon22 = Polygon(tmp_polygon2);
        humarkup_polygon2 = tmp_polygon22.buffer(0);
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
  
  ##################################
  def getMatrixValue(poly_in,patch_min_x_pixel,patch_min_y_pixel):          
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
  
  #########################################################
  def saveFeatures2Mongo(case_id,image_width,image_height,user,patch_width_index,patch_height_index,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,tumorFlag,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,grayscale_segment_mean,grayscale_segment_std,Hematoxylin_segment_mean,Hematoxylin_segment_std,grayscale_patch_10th_percentile,grayscale_patch_25th_percentile,grayscale_patch_50th_percentile,grayscale_patch_75th_percentile,grayscale_patch_90th_percentile,Hematoxylin_patch_10th_percentile,Hematoxylin_patch_25th_percentile,Hematoxylin_patch_50th_percentile,Hematoxylin_patch_75th_percentile,Hematoxylin_patch_90th_percentile,segment_10th_percentile_grayscale_intensity,segment_25th_percentile_grayscale_intensity,segment_50th_percentile_grayscale_intensity,segment_75th_percentile_grayscale_intensity,segment_90th_percentile_grayscale_intensity,segment_10th_percentile_hematoxylin_intensity,segment_25th_percentile_hematoxylin_intensity,segment_50th_percentile_hematoxylin_intensity,segment_75th_percentile_hematoxylin_intensity,segment_90th_percentile_hematoxylin_intensity):
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
    patch_feature_data['tumorFlag'] = tumorFlag;  
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
    collection_saved.insert_one(patch_feature_data);         
  ######################################################################    
  
  
  print '--- process image_list  ---- ';   
  for item in image_list:  
    case_id=item[0];
    user=item[1];    
    #exit();
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
       
    image_file = os.path.join(local_image_folder, image_file_name);
    print image_file;
    
    print " -- run OpenSlide.OpenSlide function -- ";
    try:
      img = openslide.OpenSlide(image_file);      
    except Exception as e: 
      print(e);
      print "Error exit from OpenSlide.OpenSlide function call."
      exit(); 
      
    image_width =img.dimensions[0];
    image_height =img.dimensions[1]; 
    print "-- image_width,image_height ---"; 
    print "    ",image_width,image_height;
    mmp_x=img.properties[openslide.PROPERTY_NAME_MPP_X];
    mmp_y=img.properties[openslide.PROPERTY_NAME_MPP_Y];
    print " --- openslide.PROPERTY_NAME_MPP_X,openslide.PROPERTY_NAME_MPP_Y ---";
    print mmp_x,mmp_y;
    #exit();
           
    humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user);     
    if(len(humanMarkupList_tumor) ==0 and humanMarkupList_non_tumor==0):
      print "No tumor or non tumor regions has been marked in this image by user %s." % user;
      exit();  
    comp_execution_id=getCompositeDatasetExecutionID(case_id);     
     
    for humanMarkup in humanMarkupList_tumor:
      region_area=humanMarkup.area;
      humanMarkup_bound= humanMarkup.bounds;  
      print "--humanMarkup_bound --";
      print humanMarkup_bound;    
      x1_pixel=int(humanMarkup_bound[0]*image_width);
      y1_pixel=int(humanMarkup_bound[1]*image_height);
      x2_pixel=int(humanMarkup_bound[2]*image_width);
      y2_pixel=int(humanMarkup_bound[3]*image_height);
      x1=float(humanMarkup_bound[0]);
      y1=float(humanMarkup_bound[1]);
      x2=float(humanMarkup_bound[2]);
      y2=float(humanMarkup_bound[3]);
      bound_width=x2_pixel-x1_pixel;
      bound_height=y2_pixel-y1_pixel;
      bound_width_unit=x2-x1;
      bound_height_unit=y2-y1;
      print "--x1_pixel,y1_pixel--";
      print x1_pixel,y1_pixel;
      print "--bound_width,bound_height--";
      print "    ",bound_width,bound_height;
      
      print " -- run openSlide read_region function -- ";
      try:
        tumor_region_img= img.read_region((x1_pixel, y1_pixel), 0, (bound_width, bound_height));
      except openslide.OpenSlideError as detail:
        print 'Handling run-time error:', detail  
        print "Error exit from openslide.OpenSlideError.";
        exit();
      except Exception as e: 
        print(e);
        print "Error exit from OpenSlide.read_region function call!";
        exit();
      
      x, y = np.meshgrid(np.arange(bound_width), np.arange(bound_height)) # make a canvas with coordinates
      x, y = x.flatten(), y.flatten();
      points = np.vstack((x,y)).T ;           
            
      region_img=[];
      region_img_hematoxylin=[];
      initial_grid=np.full((bound_width*bound_height), False); 
      findPixelWithinPolygon=False; 
      percent_nuclear_material=0.0; 
      segment_area_within_tumor=0.0;
      
      """    
      #loop over all nucleus within the region
      x1_new=float(x1-(bound_width_unit*tolerance));
      y1_new=float(y1-(bound_height_unit*tolerance));
      x2_new=float(x2+(bound_width_unit*tolerance));
      y2_new=float(y2+(bound_height_unit*tolerance));  
      for nuclues_polygon in objects2.find({"provenance.image.case_id":case_id,
                                            "provenance.analysis.execution_id":comp_execution_id,                                                                                                   
                                            "x" : { '$gte':x1_new, '$lte':x2_new},
                                            "y" : { '$gte':y1_new, '$lte':y2_new} },{"geometry":1,"_id":0}):         
        polygon=nuclues_polygon["geometry"]["coordinates"][0];             
        tmp_poly2=[tuple(i2) for i2 in polygon];
        computer_polygon2 = Polygon(tmp_poly2);
        computer_polygon = computer_polygon2.buffer(0);        
        polygon_area= computer_polygon.area; 
        
        if(computer_polygon.within(humanMarkup)):         
          segment_area_within_tumor = segment_area_within_tumor + polygon_area;
        elif(computer_polygon.intersects(humanMarkup)):               
          polygon_intersect=computer_polygon.intersection(humanMarkup);
          tmp_area=polygon_intersect.area;
          segment_area_within_tumor = segment_area_within_tumor + tmp_area; 
              
      percent_nuclear_material=float(segment_area_within_tumor/region_area)*100.0;
      print "--- region_area,segment_area_within_tumor,percent_nuclear_material ---";
      print region_area,segment_area_within_tumor,percent_nuclear_material;
      """
        
      grayscale_img = tumor_region_img.convert('L');
      rgb_img = tumor_region_img.convert('RGB');        
      grayscale_img_matrix=np.array(grayscale_img);  
      rgb_img_matrix=np.array(rgb_img);
      
      hed_title_img = separate_stains(rgb_img_matrix, hed_from_rgb);               
      Hematoxylin_img_matrix = [[0 for x in range(bound_width)] for y in range(bound_height)] 
      for index1,row in enumerate(hed_title_img):
        for index2,pixel in enumerate(row):
          Hematoxylin_img_matrix[index1][index2]=pixel[0];     
      
      #print bound_width,bound_height;
      polygon_intersect_points =list(zip(*humanMarkup.exterior.coords.xy));    
      tmp_polygon =[];            
      for ii in range (0,len(polygon_intersect_points)):   
        x0=polygon_intersect_points[ii][0];
        y0=polygon_intersect_points[ii][1];                 
        x01=x0*image_width-x1_pixel;
        y01=y0*image_height-y1_pixel;
        x01=int(round(x01)); 
        y01=int(round(y01));                
        point=[x01,y01];
        tmp_polygon.append(point);  
      #print len(tmp_polygon); 
      #print len(grayscale_img_matrix);
      print "--------------------";          
      if (len(tmp_polygon) >0):   
        path = Path(tmp_polygon)            
        grid = path.contains_points(points);      
        mask = grid.reshape(bound_width,bound_height); 
        #print len(mask);            
        for index1,row in enumerate(mask):
          #print len(row);
          #exit();
          for index2,pixel in enumerate(row):            
            if (pixel):#this pixel is inside of tumor_region                     
              region_img.append(grayscale_img_matrix[index2][index1]);
              region_img_hematoxylin.append(Hematoxylin_img_matrix[index2][index1]);  
      print "array length is: ";                 
      print len(region_img);
      
      if (len(region_img)>0):          
        region_mean_grayscale_intensity= np.mean(region_img);
        region_std_grayscale_intensity= np.std(region_img); 
        region_10th_percentile_grayscale_intensity=np.percentile(region_img,10); 
        region_25th_percentile_grayscale_intensity=np.percentile(region_img,25);
        region_50th_percentile_grayscale_intensity=np.percentile(region_img,50);
        region_75th_percentile_grayscale_intensity=np.percentile(region_img,75);
        region_90th_percentile_grayscale_intensity=np.percentile(region_img,90);
        region_mean_hematoxylin_intensity= np.mean(region_img_hematoxylin);
        region_std_hematoxylin_intensity= np.std(region_img_hematoxylin); 
        region_10th_percentile_hematoxylin_intensity=np.percentile(region_img_hematoxylin,10); 
        region_25th_percentile_hematoxylin_intensity=np.percentile(region_img_hematoxylin,25);
        region_50th_percentile_hematoxylin_intensity=np.percentile(region_img_hematoxylin,50);
        region_75th_percentile_hematoxylin_intensity=np.percentile(region_img_hematoxylin,75);
        region_90th_percentile_hematoxylin_intensity=np.percentile(region_img_hematoxylin,90);                    
      else:
        region_mean_grayscale_intensity="n/a";
        region_std_grayscale_intensity="n/a";
        region_mean_hematoxylin_intensity="n/a";
        region_std_hematoxylin_intensity="n/a";   
        region_10th_percentile_grayscale_intensity="n/a";
        region_25th_percentile_grayscale_intensity="n/a";
        region_50th_percentile_grayscale_intensity ="n/a"; 
        region_75th_percentile_grayscale_intensity="n/a"; 
        region_90th_percentile_grayscale_intensity ="n/a"; 
        region_10th_percentile_hematoxylin_intensity="n/a"; 
        region_25th_percentile_hematoxylin_intensity="n/a";
        region_50th_percentile_hematoxylin_intensity="n/a";
        region_75th_percentile_hematoxylin_intensity="n/a";
        region_90th_percentile_hematoxylin_intensity="n/a";
      
      print case_id,image_width,image_height,user,segment_area_within_tumor,percent_nuclear_material,region_mean_grayscale_intensity,region_std_grayscale_intensity,region_mean_hematoxylin_intensity,region_std_hematoxylin_intensity,region_50th_percentile_grayscale_intensity,region_50th_percentile_hematoxylin_intensity; 
      #exit();        
      #saveFeatures2Mongo(case_id,image_width,image_height,user,i,j,patch_min_x_pixel,patch_min_y_pixel,patch_size,patch_polygon_area,tumorFlag,nucleus_area,percent_nuclear_material,grayscale_patch_mean,grayscale_patch_std,Hematoxylin_patch_mean,Hematoxylin_patch_std,segment_mean_grayscale_intensity,segment_std_grayscale_intensity,segment_mean_hematoxylin_intensity,segment_std_hematoxylin_intensity,grayscale_patch_10th_percentile,grayscale_patch_25th_percentile,grayscale_patch_50th_percentile,grayscale_patch_75th_percentile,grayscale_patch_90th_percentile,Hematoxylin_patch_10th_percentile,Hematoxylin_patch_25th_percentile,Hematoxylin_patch_50th_percentile,Hematoxylin_patch_75th_percentile,Hematoxylin_patch_90th_percentile,segment_10th_percentile_grayscale_intensity,segment_25th_percentile_grayscale_intensity,segment_50th_percentile_grayscale_intensity,segment_75th_percentile_grayscale_intensity,segment_90th_percentile_grayscale_intensity,segment_10th_percentile_hematoxylin_intensity,segment_25th_percentile_hematoxylin_intensity,segment_50th_percentile_hematoxylin_intensity,segment_75th_percentile_hematoxylin_intensity,segment_90th_percentile_hematoxylin_intensity);   
                            
    img.close();            
  exit();  
 
