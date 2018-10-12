import json
import os
import numpy as np
import csv
import cv2
import sys
import shutil
import subprocess
import skimage.io
import time
from datetime import datetime
import concurrent.futures 
import collections
from pymongo import MongoClient
import shapely.geometry
from shapely.geometry import Polygon
import openslide


##################################################################
def read_poly_coor(poly_file, poly_field_name, label_field_name):
    poly_arr = [];
    label_arr = [];
    with open(poly_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for line_count, row in enumerate(csv_reader):
            if line_count == 0:
                # This is the title line
                polygonid = row.index(poly_field_name)
                labelid   = row.index(label_field_name)
                continue;

            # Read Polygons
            poly_str = row[polygonid];
            poly_str = poly_str[1:-1];  # This is to remove brackets at the two ends of the string
            poly_str = poly_str.split(':');

            # Map to long and subtract the offset
            poly_int = map(float, poly_str);
            poly_int = np.array(poly_int);
            poly_x = poly_int[range(0, len(poly_int), 2)];
            poly_y = poly_int[range(1, len(poly_int), 2)];
            #poly_x = poly_x.astype(np.int64);
            #poly_y = poly_y.astype(np.int64);

            # Combine x and y into array with format [[x1, y1], [x2, y2],...]
            poly = zip(poly_x, poly_y);
            poly = [list(t) for t in poly];
            if (len(poly_arr) == 0):
                poly_arr = [poly];
            else:
                poly_arr.append(poly);

            # Read labels
            lbl_str = int(row[labelid]);
            label_arr.append(lbl_str)

    return poly_arr, label_arr;
###############################################

    
####################################
def cal_patch(mask):
    # Nuclei ratio
    bin_mask = (mask > 0).astype(np.float);
    nuclei_area = np.sum(bin_mask);
    nuclei_ratio = nuclei_area / mask.size;

    # Nuclei perimeter
    polyidx_max = np.amax(mask);
    peri_arr = [];
    area_arr = []
    for poly_idx in range(polyidx_max):
        mask_nucleus = (mask == poly_idx+1).astype(np.uint8)*255;

        if (np.amax(mask_nucleus) == 0):
            # Meaning that this nucleus is not in this patch
            continue;

        # Get edge to compute perimeter
        edges = cv2.Canny(mask_nucleus, 100, 200);
        edges = (edges > 127).astype(np.uint16);
        peri_arr.append(np.sum(edges));

        # Compute area of this nucleus
        mask_nucleus_bin = (mask_nucleus > 127).astype(np.uint16);
        area_arr.append(np.sum(mask_nucleus_bin));

    if (len(area_arr) > 0):
        area_arr = np.array(area_arr);
        peri_arr = np.array(peri_arr);
        return nuclei_ratio, np.mean(area_arr), np.mean(peri_arr);
    else:
        return nuclei_ratio, 0, 0;
##################################################################


############################################################
def cal_patch_tissue(mask, tissue):
    # Mask the nuclei mask with tissue mask
    mask = np.multiply(mask, tissue);

    # Nuclei ratio
    bin_mask = (mask > 0).astype(np.float);
    nuclei_area = np.sum(bin_mask);
    if np.sum(tissue) > 0:
        nuclei_ratio = nuclei_area / np.sum(tissue);
    else:
        nuclei_ratio = 0.0;

    # Nuclei perimeter
    polyidx_max = np.amax(mask);
    peri_arr = [];
    area_arr = []
    for poly_idx in range(polyidx_max):
        mask_nucleus = (mask == poly_idx+1).astype(np.uint8)*255;

        if (np.amax(mask_nucleus) == 0):
            # Meaning that this nucleus is not in this patch
            continue;

        # Get edge to compute perimeter
        edges = cv2.Canny(mask_nucleus, 100, 200);
        edges = (edges > 127).astype(np.uint16);
        peri_arr.append(np.sum(edges));

        # Compute area of this nucleus
        mask_nucleus_bin = (mask_nucleus > 127).astype(np.uint16);
        area_arr.append(np.sum(mask_nucleus_bin));

    if (len(area_arr) > 0):
        area_arr = np.array(area_arr);
        peri_arr = np.array(peri_arr);
        return nuclei_ratio, np.mean(area_arr), np.mean(peri_arr);
    else:
        return nuclei_ratio, 0, 0;
########################################################################


##########################################################################################
def get_tumor_intersect(tumor_list, tumor_label_list, xmin, ymin, width, height, tile_offset_x, tile_offset_y):
    patch_obj = shapely.geometry.box(xmin+tile_offset_x, ymin+tile_offset_y, xmin+width-1+tile_offset_x, ymin+height-1+tile_offset_y);
    intersect = False;
    is_pos_tumor = False;
    is_neg_tumor = False;
    for tumor_idx, tumor in enumerate(tumor_list):
        print tumor.intersection(patch_obj);
        if (tumor.intersection(patch_obj)):
            print "if (tumor.intersection(patch_obj))"
            if (tumor_label_list[tumor_idx] == 1):
                is_pos_tumor = True;
            else:
                is_neg_tumor = True;
        else:
          print "else of tumor.intersection(patch_obj) ";
          
    print intersect,is_pos_tumor,is_neg_tumor;  
        
    if (is_pos_tumor == True) and (is_neg_tumor == False):
        return True;
    else:
        return False;
######################################################################################


##########################################################################################
def get_tumor_intersect_flag(xmin, ymin, width, height, tile_offset_x, tile_offset_y):    
    x1=float(tile_offset_x+xmin)/float(image_width);
    y1=float(tile_offset_y+ymin)/float(image_height);
    x2=float(tile_offset_x+xmin+width-1)/float(image_width);
    y2=float(tile_offset_y+ymin+height-1)/float(image_height);    
    patch_polygon_0=[[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]];
    tmp_poly=[tuple(i1) for i1 in patch_polygon_0];
    tmp_polygon = Polygon(tmp_poly);
    patch_obj = tmp_polygon.buffer(0);    
    
    is_tumor_patch=False;
    is_non_tumor_patch=False;
    patch_humanmarkup_intersect_polygon_tumor = Polygon([(0, 0), (1, 1), (1, 0)]);
    patch_humanmarkup_intersect_polygon_nontumor = Polygon([(0, 0), (1, 1), (1, 0)]);    
    
    for humanMarkup in humanMarkupList_tumor:                             
      if (patch_obj.within(humanMarkup)):        
        is_tumor_patch=True;  
        patch_humanmarkup_intersect_polygon_tumor=humanMarkup          
        break;
      elif (patch_obj.intersects(humanMarkup)):         
        is_tumor_patch=True; 
        patch_humanmarkup_intersect_polygon_tumor=humanMarkup          
        break;                        
            
    for humanMarkup2 in humanMarkupList_non_tumor:                              
      if (patch_obj.within(humanMarkup2)):        
        is_non_tumor_patch=True;  
        patch_humanmarkup_intersect_polygon_nontumor=humanMarkup2;           
        break;
      elif (patch_obj.intersects(humanMarkup2)):         
        is_non_tumor_patch=True;   
        patch_humanmarkup_intersect_polygon_nontumor=humanMarkup2;            
        break;
        
    # not related to tumor or non tumor region    
    if not is_tumor_patch and not is_non_tumor_patch:       
      return 0;  
      
    # related to tumor but not non tumor region
    if is_tumor_patch and not is_non_tumor_patch:      
      return 1;
    
    # not related to tumor but related to non tumor region  
    if not is_tumor_patch and is_non_tumor_patch:     
      return 2; 
      
    if is_tumor_patch and is_non_tumor_patch: # patch intersect with both tumor and non tumor region     
      if patch_humanmarkup_intersect_polygon_tumor.within(patch_humanmarkup_intersect_polygon_nontumor):#tumor is within another non tumor region
        return 1; 
      elif patch_humanmarkup_intersect_polygon_nontumor.within(patch_humanmarkup_intersect_polygon_tumor):#non_tumor is within another tumor region
        return 2;
      else:#tumor and non tumor region intersects each other
        return 1;                      
                
######################################################################################

        
###########################################################################################
def process_tile(csvfile, jsonfile, svsfile, outfiledir, outtiledir, outtissuedir): 
    # Param
    patch_width_org = 512;
    patch_height_org = 512;

    tile_name = os.path.basename(csvfile).split('-features')[0];
    outfilepath = os.path.join(outfiledir, tile_name+'-stat.csv');

    # Read json file
    with open(jsonfile) as f:
        datajson = json.load(f);
        img_width = datajson['image_width'];
        img_height = datajson['image_height'];
        tile_x = datajson['tile_minx'];
        tile_y = datajson['tile_miny'];
        tile_width = datajson['tile_width'];
        tile_height = datajson['tile_height'];
        mpp = datajson['mpp'];
        caseid = datajson['subject_id'];


    # Read csv file
    poly_arr = [];
    with open(csvfile) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for line_count, row in enumerate(csv_reader):
            if line_count == 0:
                # This is the title line
                polygonid =  row.index('Polygon')
                continue;
            poly_str = row[polygonid];
            poly_str = poly_str[1:-1];  # This is to remove brackets at the two ends of the string
            poly_str = poly_str.split(':');

            # Map to long and subtract the offset
            poly_int = map(float, poly_str);
            poly_int = np.array(poly_int);
            poly_x = poly_int[range(0, len(poly_int), 2)];
            poly_y = poly_int[range(1, len(poly_int), 2)];
            poly_x = (poly_x - tile_x).astype(np.int64);
            poly_y = (poly_y - tile_y).astype(np.int64);


            # Combine x and y into array with format [[x1, y1], [x2, y2],...]
            poly = zip(poly_x, poly_y);
            poly = [list(t) for t in poly];
            if (len(poly_arr) == 0):
                poly_arr = [poly];
            else:
                poly_arr.append(poly);

    # Convert polygons to mask
    mask = np.zeros((tile_height, tile_width), dtype=np.uint16)
    for poly_idx, single_poly in enumerate(poly_arr):
        cv2.fillConvexPoly(mask, np.array(single_poly), (poly_idx+1));

    tissue_mask = get_tissue_mask(jsonfile, svsfile, outtiledir, tile_width, tile_height, outtissuedir);            
        
    # Break the tile into patches
    with open(outfilepath, 'w') as outfile:
        writer = csv.writer(outfile);
        wrtline = ['case_id', 'image_width', 'image_height', 'mpp_x', 'mpp_y', 'patch_x', 'patch_y', 'patch_width', 'patch_height',
                   'patch_area_micro', 'nuclei_area_micro', 'nuclei_ratio', 'nucleus_material_percentage', 'nuclei_average_area', 'nuclei_average_perimeter', 'has_tumor'];
        writer.writerow(wrtline);

        for patch_x in xrange(0,tile_width,patch_width_org):
            for patch_y in xrange(0, tile_height, patch_height_org):
                patch_width  = min(tile_width - patch_x, patch_width_org);
                patch_height = min(tile_height - patch_y, patch_height_org);
                if ((patch_width == 0) or (patch_height == 0)):
                    continue;
                patch = mask[patch_y : patch_y + patch_height, patch_x : patch_x + patch_width];
                tissue_patch = tissue_mask[patch_y: patch_y + patch_height, patch_x: patch_x + patch_width];
                nu_ratio, nu_area, nu_peri = cal_patch_tissue(patch, tissue_patch);
                patch_area_micro = patch_width * patch_height * mpp * mpp;
                nu_area_micro = patch_area_micro * nu_ratio;
                nucleus_material_percentage= nu_ratio*100.0;         
                
                #has_tumor: 1--tumor;2:non_tumor;0:out of tumor and non_tumor boundry
                has_tumor = get_tumor_intersect_flag(patch_x, patch_y, patch_width, patch_height, tile_x, tile_y);
                
                wrtline = [caseid, img_width, img_height, mpp, mpp, patch_x+tile_x, patch_y+tile_y, patch_width, patch_height,
                           patch_area_micro, nu_area_micro, nu_ratio, nucleus_material_percentage,nu_area, nu_peri, has_tumor];
                writer.writerow(wrtline);
                
                saveFeatures2MongoDB(caseid,img_width, img_height, mpp, mpp, patch_x+tile_x, patch_y+tile_y, patch_width, patch_height,patch_area_micro, nu_area_micro, nu_ratio, nu_area, nu_peri,has_tumor);    
##############################################################################################


#######################################################################################################
def get_tissue_mask(jsonfile, svsfile, outtiledir, tile_width, tile_height, outtissuedir):
    # Param
    verification_patch_size = 128;

    # Check and extract tile
    tile_name = os.path.basename(jsonfile).split('-algmeta.json')[0];
    rgb_tile_path = os.path.join(outtiledir, tile_name + '-tile.png');
    xcoor = int(tile_name.split('_')[-2][1:]);
    ycoor = int(tile_name.split('_')[-1].split('-')[0][1:]);
    if not os.path.isfile(rgb_tile_path):
        cmd = 'openslide-write-png {} {} {} 0 {} {} {}'.format(svsfile, xcoor, ycoor, tile_width, tile_height, rgb_tile_path);
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE);
        process.wait();
    
    #print rgb_tile_path; 
    # Read the rgb file
    img = skimage.io.imread(rgb_tile_path).astype(np.float) / 255;  # Divide by 255 to convert to [0,1]
    tissue_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8);

    # Identify glass for each patch
    for patch_x in xrange(0, tile_width, verification_patch_size):
        for patch_y in xrange(0, tile_height, verification_patch_size):
            patch_width = min(tile_width - patch_x, verification_patch_size);
            patch_height = min(tile_height - patch_y, verification_patch_size);
            if (patch_width == 0) or (patch_height == 0):
                continue;
            patch = img[patch_y: patch_y + patch_height, patch_x: patch_x + patch_width, :];
            wh = patch[..., 0].std() + patch[..., 1].std() + patch[..., 2].std();
            if wh >= 0.20:
                tissue_mask[patch_y: patch_y + patch_height, patch_x: patch_x + patch_width] = 1;

    # Save tissue mask
    if outtissuedir is not None:
        # Save this tissue mask
        tissuefile = os.path.join(outtissuedir, tile_name + '-tissue.png');
        skimage.io.imsave(tissuefile, tissue_mask*255);

    return tissue_mask;
##########################################################################################

###########################################
def findImagePath(case_id):
  image_path="";  
  input_file="image_path.txt"
  image_path_file = os.path.join(code_base, input_file); 
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
##########################################################


#############################################
def findTumor_NonTumorRegions(case_id,user):
  execution_id=user+"_Tumor_Region";
  execution_id2=user+"_Non_Tumor_Region";
    
  #handle only tumor region overlap
  humanMarkupList_tumor=[];
  tmp_tumor_markup_list=[];
    
  for humarkup in objects.find({"provenance.image.case_id":case_id,
                                "provenance.analysis.execution_id":execution_id},
                               {"geometry":1,"_id":1}):                         
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
    humarkup_polygon1 = tmp_polygon1.convex_hull;
    humarkup_polygon1 = humarkup_polygon1.buffer(0);
    humarkup_polygon_bound1= humarkup_polygon1.bounds;
    is_within=False;
    is_intersect=False;
    for index2 in range(0, len(tmp_non_tumor_markup_list)):  
      tmp_tumor_markup2=tmp_non_tumor_markup_list[index2];                               
      humarkup_polygon_tmp2=tmp_tumor_markup2["geometry"]["coordinates"][0];             
      tmp_polygon2=[tuple(i2) for i2 in humarkup_polygon_tmp2];
      tmp_polygon22 = Polygon(tmp_polygon2);
      humarkup_polygon2=tmp_polygon22.convex_hull;
      humarkup_polygon2 = humarkup_polygon2.buffer(0);
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


##############################################
def generate_tumor_region_coordinate(coordinate_folder,image_svsfile,case_id,user):     
    
  outfilepath = os.path.join(coordinate_folder, case_id+'-tumor_region_coordinate.csv');
  if os.path.isfile(outfilepath):#delete this csv file if it exists
    os.remove(outfilepath);
              
  humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user); 
  if(len(humanMarkupList_tumor) ==0 and humanMarkupList_non_tumor==0):
    print "No tumor or non tumor regions has been marked in this image by user %s." % user;
    return;
          
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
        wrtline = [2,coordinate_str];
        writer.writerow(wrtline);
##############################################        
        
#############################################################################  
def saveFeatures2MongoDB(case_id, image_width, image_height, mpp_x, mpp_y, patch_x, patch_y, patch_width, patch_height,patch_area_micro, nuclei_area_micro, nuclei_ratio, nuclei_average_area, nuclei_average_perimeter,has_tumor):
    patch_feature_data = collections.OrderedDict();
    patch_feature_data['case_id'] = case_id;
    patch_feature_data['image_width'] = image_width;
    patch_feature_data['image_height'] = image_height;  
    patch_feature_data['mpp_x'] = mpp_x;
    patch_feature_data['mpp_y'] = mpp_y;    
    patch_feature_data['patch_x'] =patch_x;
    patch_feature_data['patch_y'] = patch_y;
    patch_feature_data['patch_width'] = patch_width; 
    patch_feature_data['patch_height'] = patch_height;       
    patch_feature_data['patch_area_micro'] = patch_area_micro;      
    patch_feature_data['nuclei_area_micro'] = nuclei_area_micro;     
    patch_feature_data['nuclei_ratio'] = nuclei_ratio;  
    nucleus_material_percentage= nuclei_ratio*100.0;  
    patch_feature_data['nucleus_material_percentage'] = nucleus_material_percentage; 
    patch_feature_data['nuclei_average_area'] = nuclei_average_area;      
    patch_feature_data['nuclei_average_perimeter'] = nuclei_average_perimeter; 
    patch_feature_data['has_tumor'] = has_tumor;     
    patch_feature_data['datetime'] = datetime.now();               
    collection_saved.insert_one(patch_feature_data); 
######################################################################################    

###############################################
def getTumorMarkupUser(case_id):
  user0="dr.rajarsi.gupta"
  string0="rajarsi.gupta";
  string1="_Tumor_Region";
  string2="_Non_Tumor_Region";
  user="";
  for record in metadata.find({"image.case_id":case_id,                 
		                           "provenance.analysis_execution_id":{'$regex' : '_Tumor_Region', '$options' : 'i'}}): 
    execution_id=record["provenance"]["analysis_execution_id"];
    if (execution_id.find(string0) <> -1):  #find it!
      if (execution_id.find(string2) <> -1):
        user=execution_id.split(string2)[0]; 
      elif (execution_id.find(string1) <> -1):
        user=execution_id.split(string1)[0];          
      break;
  return user;    
################################################# 


#####################################################################        
### login eagle cluster nfs004 in folder "/data/shared/bwang"     ###
### then switch to "/home/bwang/patch_level" to run this program  ###
#####################################################################

if __name__ == "__main__":    
  if len(sys.argv)<2:
    print "usage:python run_process_tile.py case_id user";
    exit(); 
  #get case_id and user from prompt input
  tmp_caseid= sys.argv[1]
  tmp_user= sys.argv[2]  
  
  image_list=[];
  tmp_array=[[],[]];
  tmp_array[0]=tmp_caseid;   
  tmp_array[1]=tmp_user;
  image_list.append(tmp_array); 
  
  max_workers=16;  
      
  my_home="/data1/bwang";
  code_base="/home/bwang/patch_level";  
  remote_dataset_folder="nfs004:/data/shared/bwang/composite_dataset_merged"     
  remote_image_folder ="nfs001:/data/shared/tcga_analysis/seer_data/images";   
  
  print " --- read config.json file ---" ;
  config_json_file_name = "config_cluster.json";  
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
  
  db2 = client[db_name2];    
  images2 =db2.images; 
  metadata2=db2.metadata;
  objects2 = db2.objects; 
      
  collection_saved= db2.patch_level_features_new;
  
  #setup local folders 
  local_dataset_folder=os.path.join(my_home, 'SEER_VTR_dataset');
  if not os.path.exists(local_dataset_folder):
    print '%s folder do not exist, then create it.' % local_dataset_folder;
    os.makedirs(local_dataset_folder);  
    
  local_image_folder = os.path.join(my_home, 'SEER_VTR_image'); 
  if not os.path.exists(local_image_folder):
    print '%s folder do not exist, then create it.' % local_image_folder;
    os.makedirs(local_image_folder);  
    
  local_output_folder = os.path.join(my_home, 'SEER_VTR_output'); 
  if not os.path.exists(local_output_folder):
    print '%s folder do not exist, then create it.' % local_output_folder;
    os.makedirs(local_output_folder);     
      
  print '--- process image_list  ---- ';   
  for item  in image_list:  
    case_id=item[0];
    user=item[1]; 
    print case_id, user;       
      
    output_folder = os.path.join(local_output_folder, case_id); 
    if not os.path.exists(output_folder):
      print '%s folder do not exist, then create it.' % output_folder;
      os.makedirs(output_folder);
        
    output_tile_folder = os.path.join(output_folder, 'tiles');
    if not os.path.exists(output_tile_folder):
      print '%s folder do not exist, then create it.' % output_tile_folder;
      os.makedirs(output_tile_folder);
    
    output_tissue_folder=output_tile_folder;
    
    #copy composite dataset from remote folder to local folder  
    remote_dataset_folder_detail = os.path.join(remote_dataset_folder, case_id);  
    local_dataset_folder_detail  = os.path.join(local_dataset_folder, case_id);
    if not os.path.exists(local_dataset_folder_detail):
        print '%s folder do not exist, then create it.' % local_dataset_folder_detail;
        os.makedirs(local_dataset_folder_detail); 
               
    if os.path.isdir(local_dataset_folder_detail) and len(os.listdir(local_dataset_folder_detail)) > 0: 
      print " all csv and json files of this image have been copied from data node.";
    else:
      subprocess.call(['scp', remote_dataset_folder_detail+'/*.json',local_dataset_folder_detail]);
      subprocess.call(['scp', remote_dataset_folder_detail+'/*features.csv',local_dataset_folder_detail]);        
  
    #copy imagwe svs file from remote folder to local folder     
    image_file_name=case_id+".svs";
    image_file = os.path.join(local_image_folder, image_file_name);         
    if not os.path.isfile(image_file):
      print "image svs file is not available, then download it to local folder.";
      img_path=findImagePath(case_id);
      full_image_file = os.path.join(remote_image_folder, img_path);      
      subprocess.call(['scp', full_image_file,local_image_folder]);   
    else:
      print "image svs file is available in folder!"         
    
    #open image file with open slide to get meta data      
    try:
      img = openslide.OpenSlide(image_file);      
    except Exception as e: 
      print(e);
      continue; 
      
    image_width =img.dimensions[0];
    image_height =img.dimensions[1];     
    
    #get human markup data  
    humanMarkupList_tumor,humanMarkupList_non_tumor=findTumor_NonTumorRegions(case_id,user);       
    if(len(humanMarkupList_tumor) ==0 and humanMarkupList_non_tumor==0):
      print "No tumor or non tumor regions has been marked in this image by user %s." % user;
      continue;   
         
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:  
      dataset_folder_by_case_id = os.path.join(local_dataset_folder, case_id);
      json_filename_list = [f for f in os.listdir(dataset_folder_by_case_id) if f.endswith('.json')] ; 
      for json_filename in json_filename_list:        
        json_file_path=os.path.join(dataset_folder_by_case_id, json_filename);        
        csv_file=json_filename.replace('-algmeta.json','-features.csv');
        csv_file_path=os.path.join(dataset_folder_by_case_id, csv_file);
        if not os.path.isfile(csv_file_path):
          print "can NOT find matching csv file from json file", case_id,json_filename;
          continue;             
        executor.submit(process_tile,csv_file_path, json_file_path, image_file, output_folder, output_tile_folder, output_tissue_folder);          
  exit();      
    
