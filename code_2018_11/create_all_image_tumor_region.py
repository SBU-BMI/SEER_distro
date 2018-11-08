from shapely.geometry import Polygon
from pymongo import MongoClient
import openslide
import csv
import sys
import os
import json
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_tumor_region.py image_user_list";
    exit();  
  
  image_user_list_name = sys.argv[1];  
   
  my_home="/home/bwang/patch_level"
    
  print " --- read config.json file ---" ;
  config_json_file_name = "config_cluster.json";  
  config_json_file = os.path.join(my_home, config_json_file_name);
  with open(config_json_file) as json_data:
    d = json.load(json_data);     
    patch_size =  d['patch_size'];   
    db_host = d['db_host'];
    db_port = d['db_port'];
    db_name1 = d['db_name1']; 
    db_name2 = d['db_name2'];
    print patch_size,db_host,db_port,db_name1,db_name2;
    
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name1]; 
  images = db.images; 
  objects = db.objects;       
  
  print '--- read image_user_list file ---- ';  
  index=0;
  image_list=[];  
  image_list_file = os.path.join(my_home, image_user_list_name);  
  with open(image_list_file, 'r') as my_file:
    reader = csv.reader(my_file, delimiter=',')
    my_list = list(reader);
    for each_row in my_list: 
      tmp_array=[[],[]]
      #print each_row[0];
      tmp_array[0]=each_row[0];   
      tmp_array[1]=each_row[1];           
      image_list.append(tmp_array);                
  print "total rows from image_list file is %d " % len(image_list) ; 
  #print image_list;
  
  local_output_folder = os.path.join(my_home, 'SEER_VTR_coordinate'); 
  if not os.path.exists(local_output_folder):
    print '%s folder do not exist, then create it.' % local_output_folder;
    os.makedirs(local_output_folder); 
  
  #######################################
  def handMultiPolygon(polygon_list):
    tmp_polygon_list=[];  
    for poly in polygon_list:    
      if poly.geom_type  == 'Polygon':
        tmp_polygon_list.append(poly);
      elif poly.geom_type  == 'MultiPolygon':
        allparts = [p.buffer(0) for p in poly.geometry]
        poly.geometry = shapely.ops.cascaded_union(allparts)
        ext_polygon_points =list(zip(*poly.geometry.exterior.coords.xy)); 
        newPoly = Polygon(ext_polygon_points);
        tmp_polygon_list.append(newPoly);
         
    return tmp_polygon_list;
  ######################################
      
  #############################################
  def findTumor_NonTumorRegions(case_id,user):
    execution_id=user+"_Tumor_Region";
    execution_id2=user+"_Non_Tumor_Region";
    
    #handle only tumor region overlap
    humanMarkupList_tumor=[];
    tmp_tumor_markup_list0=[];
    
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id},
                                 {"geometry":1,"_id":1}): 
      humarkup_polygon_tmp=humarkup["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i2) for i2 in humarkup_polygon_tmp];
      tmp_polygon2=Polygon(tmp_polygon); 
      tmp_polygon2=tmp_polygon2.convex_hull;       
      tmp_polygon2=tmp_polygon2.buffer(0);                                                  
      tmp_tumor_markup_list0.append(tmp_polygon2);
          
    #handle MultiPolygon
    tmp_tumor_markup_list=handMultiPolygon(tmp_tumor_markup_list0);   
              
    index_intersected=[];                                
    for index1 in range(0, len(tmp_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      humarkup_polygon1=tmp_tumor_markup_list[index1];         
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_tumor_markup_list)):  
        humarkup_polygon2=tmp_tumor_markup_list[index2];
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
    tmp_non_tumor_markup_list0=[];
    for humarkup in objects.find({"provenance.image.case_id":case_id,
                                  "provenance.analysis.execution_id":execution_id2},
                                 {"geometry":1,"_id":0}):
      humarkup_polygon_tmp=humarkup["geometry"]["coordinates"][0];             
      tmp_polygon=[tuple(i2) for i2 in humarkup_polygon_tmp];
      tmp_polygon2=Polygon(tmp_polygon); 
      tmp_polygon2=tmp_polygon2.convex_hull;       
      tmp_polygon2=tmp_polygon2.buffer(0);
      tmp_non_tumor_markup_list0.append(tmp_polygon2);   
      
    #handle MultiPolygon
    tmp_non_tumor_markup_list=handMultiPolygon(tmp_non_tumor_markup_list0);      
    index_intersected=[];                                
    for index1 in range(0, len(tmp_non_tumor_markup_list)):  
      if index1 in index_intersected :#skip polygon,which is been merged to another one
        continue;
      humarkup_polygon1=tmp_non_tumor_markup_list[index1]; 
      is_within=False;
      is_intersect=False;
      for index2 in range(0, len(tmp_non_tumor_markup_list)):  
        humarkup_polygon2=tmp_non_tumor_markup_list[index2];
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
  ##############################################   
  
  ###############################################
  def getImageWidthHeight(case_id): 
    image_width="";
    image_height="";   
    for record in images.find({"case_id":case_id},{"width":1,"height":1,"_id":0}):
      image_width=record["width"];
      image_height=record["height"];
      break;
    return image_width,image_height;    
  ################################################# 
          
  print '--- process image_list  ---- ';   
  for item  in image_list:  
    case_id=item[0];
    user=item[1];     
    image_width,image_height = getImageWidthHeight(case_id);
    print image_width,image_height;   
    #exit();
    outfilepath = os.path.join(local_output_folder, case_id+'-tumor_region_coordinate.csv');
    
    humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user); 
    if(len(humanMarkupList_tumor) ==0 and humanMarkupList_non_tumor==0):
      print "No tumor or non tumor regions has been marked in this image by user %s." % user;
      continue;
          
    with open(outfilepath, 'w') as outfile:
      writer = csv.writer(outfile);
      wrtline = ['tumor_flag','polygon'];
      writer.writerow(wrtline);            
        
      for humanMarkup in humanMarkupList_tumor:     
        polygon_points =list(zip(*humanMarkup.exterior.coords.xy));        
        coordinate_str="["
        for i in range (0,len(polygon_points)):   
          x=polygon_points[i][0];
          y=polygon_points[i][1]; 
          x1=x*float(image_width)
          y1=x*float(image_height)
          x2=round(x1,1)
          y2=round(y1,1)          
          if i< len(polygon_points)-1:
            coordinate_str=coordinate_str+ str(x2)+":"+ str(y2) + ":";  
          else:
            coordinate_str=coordinate_str+ str(x2)+":"+ str(y2);            
        coordinate_str=coordinate_str+"]"        
        wrtline = [1,coordinate_str];
        writer.writerow(wrtline); 
        
      for humanMarkup in humanMarkupList_non_tumor:     
        polygon_points =list(zip(*humanMarkup.exterior.coords.xy));        
        coordinate_str="["
        for i in range (0,len(polygon_points)):   
          x=polygon_points[i][0];
          y=polygon_points[i][1]; 
          x1=x*float(image_width)
          y1=x*float(image_height)
          x2=round(x1,1)
          y2=round(y1,1)          
          if i< len(polygon_points)-1:
            coordinate_str=coordinate_str+ str(x2)+":"+ str(y2) + ":";  
          else:
            coordinate_str=coordinate_str+ str(x2)+":"+ str(y2);            
        coordinate_str=coordinate_str+"]"        
        wrtline = [0,coordinate_str];
        writer.writerow(wrtline);         
    
  exit();  
 
