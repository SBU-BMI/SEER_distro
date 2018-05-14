from pymongo import MongoClient
from shapely.geometry import LineString
from shapely.geometry.polygon import LinearRing
from shapely.geometry import Polygon
from shapely.affinity import affine_transform
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
from skimage.color import separate_stains,hdx_from_rgb
from skimage import data

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_patient_level_dataset.py config.json";
    exit();  
  
  start_time = time.time(); 
  csv.field_size_limit(sys.maxsize);  
  
  ihc = data.immunohistochemistry();
  print ihc;
  print ihc.shape;
  ihc_hdx = separate_stains(ihc, hdx_from_rgb);
  print ihc_hdx;
  print ihc_hdx.shape;
  #exit();  
  
  remote_folder="nfs001:/data/shared/tcga_analysis/seer_data/results";  
  my_home="/home/bwang/patient_level";
  local_folder = os.path.join(my_home, 'results');  
  
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
    db_name = d['db_name']; 
    print image_list_file,patch_size,db_host,db_port,db_name;
  #exit();
  
  print '--- read image_user_list file ---- ';  
  index=0;
  image_list=[];  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list: 
      print each_row[0];             
      image_list.append(each_row[0]);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  print image_list;
  #exit();  
  
  print '--- read caseid_perfix_algorithm file ---- ';
  input_file="caseid_perfix_algorithm.txt"
  analysis_list_csv = os.path.join(my_home, input_file);         
  if not os.path.isfile(analysis_list_csv):
    print "caseid_perfix_algorithm file is not available."
    exit();   
  index=0;
  analysis_list=[];   
  with open(analysis_list_csv, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list:      
      tmp_analysis_list=[[],[],[]]; 
      tmp_analysis_list[0]= each_row[0];#case_id
      tmp_analysis_list[1]= each_row[1];#prefix
      tmp_analysis_list[2]= each_row[2];#algorithm   
      analysis_list.append(tmp_analysis_list);                
  print "total rows from master csv file is %d " % len(analysis_list) ; 
  #exit();
  
  def findFirstPrefix(case_id):
    prefix="";    
    for tmp in analysis_list:
      case_id_row=tmp[0];
      prefix_row=tmp[1];      
      if (case_id_row == case_id):
          prefix =prefix_row;     
          break
    return  prefix; 
  
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;     
  
  image_width=0;
  image_height=0;  
  x0=0.0;
  y0=0.0
  tolence=0.05;
  patch_x_num=0; 
  patch_y_num=0;
  
  print '--- process image_list  ---- ';   
  for item in image_list:  
    case_id=item;
    #download png and json file to local folder
    remote_img_folder = os.path.join(remote_folder, case_id);
    image_file_name=case_id+".svs";
    img_folder = os.path.join(my_home, 'img');
    image_file = os.path.join(img_folder, image_file_name);
    
    prefix=findFirstPrefix(case_id);    
    #for prefix in os.listdir(remote_img_folder):
      #print prefix;
    #exit();    
    #ls = subprocess.Popen(['ssh','nfs001:/data/shared/tcga_analysis/seer_data/results/17039790', 'ls'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #out, err =  ls.communicate()
    #print out
    #print err   
    #exit();
      
    detail_remote_folder = os.path.join(remote_img_folder, prefix);    
    local_img_folder = os.path.join(local_folder, case_id);    
    if not os.path.exists(local_img_folder):
      print '%s folder do not exist, then reate it.' % local_img_folder;
      os.makedirs(local_img_folder);        
    if os.path.isdir(local_img_folder) and len(os.listdir(local_img_folder)) > 0: 
      print " all png and json files have been copied from remote data node.";
    else:
      subprocess.call(['scp', detail_remote_folder+'/*.json',local_img_folder]);
      subprocess.call(['scp', detail_remote_folder+'/*.png',local_img_folder]); 
    #exit(); 
    
    """
    png_filename_list = [f for f in os.listdir(local_img_folder) if f.endswith('.png')] ;
    print 'there are %d png files in this folder.' % len(png_filename_list);
    for png_filename in png_filename_list:  
      #print png_filename;
      png_file = os.path.join(local_img_folder, png_filename);
      img = color.rgb2gray(io.imread(png_file));
      #Notes: The weights used in this conversion are calibrated for contemporary CRT phosphors: Y = 0.2125 R + 0.7154 G + 0.0721 B
      #print img;
      #print len(img);
      #print '-----';
      #grayscale_intensity=0.0;
      #for index1,row in enumerate(img):
        #print len(row);
        #print row;
        #for index2,colum in enumerate(row):
          #grayscale_intensity = grayscale_intensity + colum;
          #if (colum> 0):
            #print index1,index2,colum;
      #mean_grayscale_intensity = grayscale_intensity / ((index1+1)*(index2+1)) ;      
      mean_grayscale_intensity= np.mean(img);
      std_grayscale_intensity= np.std(img);
      #print (index1+1),(index2+1), grayscale_intensity; 
      print png_filename, mean_grayscale_intensity,std_grayscale_intensity;   
      #exit();
    exit();
    """
    #get execution_id
    execution_id="";
    for record in metadata.find({"image.case_id":case_id,                 
				                         "provenance.analysis_execution_id":{'$regex' : 'composite_dataset', '$options' : 'i'}}): 
      execution_id=record["provenance"]["analysis_execution_id"];
    print "execution_id is %s." % execution_id;
        
    json_filename_list = [f for f in os.listdir(local_img_folder) if f.endswith('.json')] ;
    print 'there are %d json files in this folder.' % len(json_filename_list);            
    tmp_title_polygon=[];      
    for json_filename in json_filename_list[0:1]:  
      print "";
      print  "------------------- json_filename ------------------------------";
      print  json_filename;          
      with open(os.path.join(local_img_folder, json_filename)) as f:
        data = json.load(f);
        analysis_id=data["analysis_id"];
        image_width=data["image_width"];
        image_height=data["image_height"];
        tile_minx=data["tile_minx"];
        tile_miny=data["tile_miny"];
        tile_width=data["tile_width"];
        tile_height=data["tile_height"];
        print "    ----- image_width,image_height,tile_minx,tile_miny,tile_width,tile_height ----";
        print image_width,image_height,tile_minx,tile_miny,tile_width,tile_height;
        title_polygon1=[[float(tile_minx)/float(image_width),float(tile_miny)/float(image_height)],[float(tile_minx+tile_width)/float(image_width),float(tile_miny)/float(image_height)],[float(tile_minx+tile_width)/float(image_width),float(tile_miny+tile_height)/float(image_height)],[float(tile_minx)/float(image_width),float(tile_miny+tile_height)/float(image_height)],[float(tile_minx)/float(image_width),float(tile_miny)/float(image_height)]];
        tmp_poly=[tuple(i1) for i1 in title_polygon1];
        tmp_polygon = Polygon(tmp_poly);
        title_polygon = tmp_polygon.buffer(0);
        #title_polygon_bound= title_polygon.bounds;
        title_polygon_area=title_polygon.area;
        tmp_list=[[],[]];
        tmp_list[0]=json_filename;
        tmp_list[1]=title_polygon;
        tmp_title_polygon.append(tmp_list);         
        x1=float(tile_minx)/float(image_width);
        y1=float(tile_miny)/float(image_height);
        x2=float(tile_minx+tile_width)/float(image_width);
        y2=float(tile_miny+tile_height)/float(image_height);        
        x1_new=x1-(x1*tolence);
        y1_new=y1-(y1*tolence);
        x2_new=x2+(x2*tolence);
        y2_new=y2+(y2*tolence); 
        #print  "-- x1_new,y1_new,x2_new,y2_new --";
        #print  x1_new,y1_new,x2_new,y2_new;
        png_filename=json_filename.replace('algmeta.json','seg.png');  
        print "     ---- png_filename is %s" %png_filename;
        png_file = os.path.join(local_img_folder, png_filename); 
        #input_img=io.imread(png_file);
        #print input_img;
        #print input_img.shape;
        #if input_img.ndim == 2:
          #input_img2 = np.expand_dims(input_img, axis=2);        
        #print input_img2;
        #print input_img2.shape; 
        #exit()
        title_img = color.rgb2gray(io.imread(png_file)); 
        x, y = np.meshgrid(np.arange(tile_width), np.arange(tile_height)) # make a canvas with coordinates
        x, y = x.flatten(), y.flatten();
        points = np.vstack((x,y)).T ;
        segment_img=[];
        #exit(); 
        nucleus_area=0.0;
        record_count =objects.find({"provenance.image.case_id":case_id,
                                    "provenance.analysis.execution_id":execution_id, 
                                    "provenance.analysis.source":"computer",
                                    "object_type":"nucleus",                                                     
                                    "x" : { '$gte':x1_new, '$lte':x2_new},
                                    "y" : { '$gte':y1_new, '$lte':y2_new} }).count();
        print "   find segmented unclei %d." %  record_count;   
        if (record_count>0):                                                   
          for nuclues_polygon in objects.find({"provenance.image.case_id":case_id,
                                             "provenance.analysis.execution_id":execution_id, 
                                             "provenance.analysis.source":"computer",
                                             "object_type":"nucleus",                                                     
                                             "x" : { '$gte':x1_new, '$lte':x2_new},
                                             "y" : { '$gte':y1_new, '$lte':y2_new} },{"geometry":1,"_id":0}):
            polygon=nuclues_polygon["geometry"]["coordinates"][0];             
            tmp_poly2=[tuple(i2) for i2 in polygon];
            computer_polygon2 = Polygon(tmp_poly2);
            computer_polygon = computer_polygon2.buffer(0);
            #computer_polygon_bound= computer_polygon.bounds;
            polygon_area= computer_polygon.area;
            new_polygon =[];           
            if (computer_polygon.within(title_polygon)):
              print "-- within --"  
              nucleus_area=nucleus_area+polygon_area;              
              for ii in range (0,len(polygon)):   
                x0=polygon[ii][0];
                y0=polygon[ii][1]; 
                #print "x0,y0";
                #print x0,y0; 
                x01=(x0*image_width)- tile_minx;
                y01=(y0*image_height)- tile_miny;
                x01=int(round(x01)); 
                y01=int(round(y01));
                #print "x01,y01"; 
                #print x01,y01;
                point=[x01,y01];
                new_polygon.append(point);               
                #exit(); 
              #print new_polygon; 
              #exit();
            elif (computer_polygon.intersects(title_polygon)):
              print "-- intersects --" 
              #for index1,row in enumerate(title_img):
                #for index2,colum in enumerate(row):
                  #if (colum> 0):
                    #print index1,index2,colum;
              #print "-------------------------";      
              tmp_intersect=computer_polygon.intersection(title_polygon);
              tmp_area=tmp_intersect.area;
              nucleus_area=nucleus_area+tmp_area;
              #print  tmp_intersect ; 
              #print "-------------------------";
              matrix2d = (image_width, 0, 0, image_height, -tile_minx, -tile_miny)
              polygon_intersect = affine_transform(tmp_intersect, matrix2d);
              #print polygon_intersect;  
              #print "-------------------------";
              #polygon_intersect_points = np.array(polygon_intersect)
              #print polygon_intersect_points;  
              #print "-------------------------"; 
              #print list(zip(*polygon_intersect.exterior.coords.xy)); 
              polygon_intersect_points =list(zip(*polygon_intersect.exterior.coords.xy));
              #print polygon_intersect_points;
              #print "-------------------------";
              #exit();            
              for jj in range (0,len(polygon_intersect_points)):   
                x0=polygon_intersect_points[jj][0];
                y0=polygon_intersect_points[jj][1]; 
                #print x0,y0;
                x01=int(round(x0)); 
                y01=int(round(y0));
                #print x01,y01;
                tmp_point=[x01,y01];
                new_polygon.append(tmp_point);
              #print new_polygon,len(new_polygon); 
            
            if (len(new_polygon) >0):             
              #print points;
              #print "-------------------------";
              p = Path(new_polygon) # make a polygon
              grid = p.contains_points(points);
              #print grid,len(grid);
              #print "-------------------------";
              #for index1,item in enumerate(grid):
                #if (item):
                  #print index1,item;            
              #print "-------------------------";
              mask = grid.reshape(tile_width,tile_height) # now you have a mask with points inside a polygon   
              #print mask,len(mask); 
              #print "-------------------------";
              for index1,row in enumerate(mask):
                for index2,pixel in enumerate(row):
                  if (pixel):#this pixel is inside of segmented unclei polygon
                    #print index1,index2,colum,title_img[index1][index2]; 
                    segment_img.append(title_img[index1][index2]);                
              #print "-------------------------";
              #exit(); 
            
        #print len(segment_img); 
        print "   --------------"; 
        if (len(segment_img)>0):
          segment_mean_grayscale_intensity= np.mean(segment_img);
          segment_std_grayscale_intensity= np.std(segment_img); 
          print "    --segment_mean_grayscale_intensity,segment_std_grayscale_intensity--"; 
          print segment_mean_grayscale_intensity,segment_std_grayscale_intensity;
        else:
          print "   No segment unclei find in this tile." ;
          
        print "   --------------";  
        mean_grayscale_intensity= np.mean(title_img);
        std_grayscale_intensity= np.std(title_img);
        print "   mean_grayscale_intensity,std_grayscale_intensity";
        print mean_grayscale_intensity,std_grayscale_intensity; 
        
        print "   --------------";
        percent_nuclear_material =(nucleus_area/title_polygon_area)*100; 
        print  "    --- title_polygon_area,nucleus_area,percent_nuclear_material  --";      
        print  title_polygon_area,nucleus_area,percent_nuclear_material;  
        
        print "   --------------";
        input_img=io.imread(png_file,as_grey=True);
        print input_img;
        print input_img.shape;
        print "   --------------"; 
        for index1,row in enumerate(input_img):
          for index2,pixel in enumerate(row):
            if pixel<>0:
              print index1,index2,pixel;
        print "   --------------";      
        for index1,row in enumerate(title_img):
          for index2,pixel in enumerate(row):
            if pixel<>0:
              print index1,index2,pixel;      
        #print "   --------------";
        #print rgb_tile_img.shape;
        #for index1,row in enumerate(rgb_tile_img):
          #print index1,row;
        #print "   --------------";
        #ihc = rgb_tile_img.immunohistochemistry();
        #hdx_title_img = separate_stains(ihc, hdx_from_rgb);
        #print hdx_title_img;
        #print rgb_tile_img.shape;
        #print rgb_tile_img,len(rgb_tile_img);
        #print rgb_tile_img.ndim;
        #if rgb_tile_img.ndim == 2:
          #rgb_tile_img = np.expand_dims(rgb_tile_img, axis=2);
        #print rgb_tile_img.shape;  
        #for index1,row in enumerate(rgb_tile_img):
          #print index1,row;  
        #print rgb_tile_img,len(rgb_tile_img);
        #rgb_tile_img =np.atleast_3d(rgb_tile_img);
        #print rgb_tile_img.ndim;
        #for index1,row in enumerate(rgb_tile_img):
          #print index1,len(row);
          #for index2,pixel in enumerate(row):
            #print index1,index2,pixel;
        #rgb_tile_img = color.rgb2gray(io.imread(png_file));     
        #hdx_title_img = separate_stains(rgb_tile_img, hdx_from_rgb);
        #print hdx_title_img; 
        #mean_hdx_intensity= np.mean(hdx_title_img);
        #std_hdx_intensity= np.std(hdx_title_img);
        #print  "    --- mean_hdx_intensity,std_hdx_intensity  --";      
        #print  mean_hdx_intensity,std_hdx_intensity;                       
  #end of  process image_list      
  exit();  
           
  """     
  x, y = np.meshgrid(np.arange(300), np.arange(300)) # make a canvas with coordinates
  x, y = x.flatten(), y.flatten()
  points = np.vstack((x,y)).T 
  p = Path(polygon) # make a polygon
  grid = p.contains_points(img);
  mask = grid.reshape(len(img),len(img)) # now you have a mask with points inside a polygon   
  print mask;
  exit();
  
          
    exit();      
    #print "process case_id %s " %case_id;
    #find execution_id
    execution_id="";
    for record in metadata.find({"image.case_id":case_id,                 
				                         "provenance.analysis_execution_id":{'$regex' : 'composite_dataset', '$options' : 'i'}}): 
      execution_id=record["provenance"]["analysis_execution_id"];
      #print  case_id, execution_id;
    #find image width and height
    for record in images.find({"case_id":case_id}):
      image_width=record["width"];
      image_height= record["height"];      
    patch_x_num=math.ceil(image_width/patch_size) ;
    patch_y_num=math.ceil(image_height/patch_size) ;  
    patch_x_num =int(patch_x_num);
    patch_y_num =int(patch_y_num);  
    print "-- case_id,image_width,image_height,patch_size, patch_x_num, patch_y_num --";     
    print case_id,image_width,image_height,patch_size, patch_x_num, patch_y_num; 
    print "--- min_x,min_y,max_x,max_y,percentage_of_nuclear_material ---";       
    for i in range(0,patch_x_num):
      for j in  range (0,patch_y_num):         
        x10=(x0+i*patch_size)/image_width;
        y10=(y0+j*patch_size)/image_height;
        x20=(x0+(i+1)*patch_size)/image_width;
        y20=(y0+(j+1)*patch_size)/image_height;
        patch_polygon1=[[x10,y10],[x20,y10],[x20,y20],[x10,y20],[x10,y10]];
        tmp_poly=[tuple(i1) for i1 in patch_polygon1];
        tmp_polygon = Polygon(tmp_poly);
        patch_polygon = tmp_polygon.buffer(0);
        patch_polygon_bound= patch_polygon.bounds;
        patch_polygon_area=patch_polygon.area;
        #print "patch_polygon coordinates  is %s" %patch_polygon;
        #print patch_polygon_bound;
        #print "patch_polygon_area is %s" % patch_polygon_area;
        #print x1,y1,x2,y2;
        #exit();
        x1=x10-(x10*tolence);
        y1=y10-(y10*tolence);
        x2=x20+(x20*tolence);
        y2=y20+(y20*tolence);
        #print "--- i,j, x1,y1,x2,y2 --";
        #print i,j,x1,y1,x2,y2; 
        nucleus_area=0.0;           
        for nuclues_polygon in objects.find({"provenance.image.case_id":case_id,
                                             "provenance.analysis.execution_id":execution_id, 
                                             "provenance.analysis.source":"computer",
                                             "object_type":"nucleus",                                                     
                                             "x" : { '$gte':x1, '$lte':x2},
                                             "y" : { '$gte':y1, '$lte':y2} }): 
          #print i,j,x1,y1,x2,y2; 
          #print "------------------"; 
          x=nuclues_polygon["x"];
          y=nuclues_polygon["y"];
          polygon=nuclues_polygon["geometry"]["coordinates"][0];
          tmp_poly2=[tuple(i2) for i2 in polygon];
          computer_polygon2 = Polygon(tmp_poly2);
          computer_polygon = computer_polygon2.buffer(0);
          computer_polygon_bound= computer_polygon.bounds;
          #print i,j,x,y,computer_polygon_bound
          polygon_area= computer_polygon.area;  
          #print "computer_polygon area calculated is %s" % polygon_area_new;        
          nv_list = nuclues_polygon['properties']['scalar_features'][0]['nv'];
          for item in nv_list:            
            if(item['name'] == "SizeInPixels"):              
              polygon_area_old1 = item['value']; 
              polygon_area_old = polygon_area_old1/(image_width*image_height) ;       
          #print i,j,polygon_area_new, polygon_area_old;   
          #print "computer_polygon area from db is %s" % polygon_area_old; 
          #print computer_polygon;               
          if (computer_polygon.within(patch_polygon)):   
            nucleus_area=nucleus_area+polygon_area;
            #print "--within--";
          elif (computer_polygon.intersects(patch_polygon)): 
             tmp_intersect=computer_polygon.intersection(patch_polygon);
             tmp_area=tmp_intersect.area;
             nucleus_area=nucleus_area+tmp_area; 
             #print "--intersection--"; 
          #elif (computer_polygon.contains(patch_polygon)):  
             #print "--contain--"; 
          #elif (computer_polygon.crosses(patch_polygon)):  
             #print "--crosses--";  
          #elif (computer_polygon.disjoint(patch_polygon)):  
             #print "--disjoint--";  
          #elif (computer_polygon.touches(patch_polygon)):  
             #print "--touches--";  
        if(nucleus_area > 0.0):     
          #print "--- i,j, min_x,min_y,max_x,max_y, patch_polygon_area , nucleus_area, percentage of nuclear material ---";  
          percent_nuclear_material =  (nucleus_area/patch_polygon_area)*100;      
          print  x10,y10,x20,y20,percent_nuclear_material;                       
  exit();  
  """                                                              
   
