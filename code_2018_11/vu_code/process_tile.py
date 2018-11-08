import json
import os
import numpy as np
import csv
import cv2
import subprocess
import skimage
import time
import shapely
import shapely.geometry
from cal_pyradiomics import *

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

def get_tumor_intersect(tumor_list, tumor_label_list, xmin, ymin, width, height, tile_offset_x, tile_offset_y):
    patch_obj = shapely.geometry.box(xmin+tile_offset_x, ymin+tile_offset_y, xmin+width-1+tile_offset_x, ymin+height-1+tile_offset_y);
    intersect = False;
    is_pos_tumor = False;
    is_neg_tumor = False;
    contain_pos_tumor = False;
    contain_neg_tumor = False;
    for tumor_idx, tumor in enumerate(tumor_list):
        if (tumor.intersection(patch_obj)):
            if (tumor_label_list[tumor_idx] == 1):
                is_pos_tumor = True;
            else:
                is_neg_tumor = True;

        if (tumor.contains(patch_obj)):
            if (tumor_label_list[tumor_idx] == 1):
                contain_pos_tumor = True;
            else:
                contain_neg_tumor = True;


    if contain_neg_tumor == False:
        if (is_pos_tumor == True) or (contain_pos_tumor == True):
            return True;
        else:
            return False;
    else:
        return False;




def process_tile(csvfile, jsonfile, outfiledir, svsfile, outtiledir, outtissuedir, tumorfile, pyradiomics_ins):
    #csvfile  = '/Users/vuhoangnguyen/Desktop/Bridge_files/PC_058_0_1.PC_058_0_1.981790050_mpp_0.2464_x34816_y24576-features.csv';
    #jsonfile = '/Users/vuhoangnguyen/Desktop/Bridge_files/PC_058_0_1.PC_058_0_1.981790050_mpp_0.2464_x34816_y24576-algmeta.json';
    #outfiledir = '/Users/vuhoangnguyen/Desktop/Bridge_files/';

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
        tile_x = datajson['patch_minx'];
        tile_y = datajson['patch_miny'];
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

    image, tissue_mask = get_tissue_mask(jsonfile, svsfile, outtiledir, tile_width, tile_height, outtissuedir);


    # Read polygons of tumor
    tumor_list_raw, tumor_label = read_poly_coor(tumorfile, 'polygon', 'tumor_flag');
    tumor_list = [];
    for tumor_idx, single_tumor in enumerate(tumor_list_raw):
        tumor_obj = shapely.geometry.Polygon(single_tumor);
        tumor_list.append(tumor_obj);

    # Break the tile into patches
    with open(outfilepath, 'w') as outfile:
        writer = csv.writer(outfile);
        wrtline = ['case_id', 'image_width', 'image_height', 'mpp_x', 'mpp_y', 'patch_x', 'patch_y', 'patch_width', 'patch_height',
                   'patch_area_micro', 'nuclei_area_micro', 'nuclei_ratio', 'nuclei_average_area', 'nuclei_average_perimeter', 'has_tumor'];

        # For pyradiomics
        wrtline = wrtline + ['fg_' + s for s in pyradiomics_ins.get_feature_name_list()] + ['bg_' + s for s in pyradiomics_ins.get_feature_name_list()]

        writer.writerow(wrtline);

        for patch_x in xrange(0,tile_width,patch_width_org):
            for patch_y in xrange(0, tile_height, patch_height_org):
                patch_width  = min(tile_width - patch_x, patch_width_org);
                patch_height = min(tile_height - patch_y, patch_height_org);
                if ((patch_width == 0) or (patch_height == 0)):
                    continue;
                patch = mask[patch_y : patch_y + patch_height, patch_x : patch_x + patch_width];
                tissue_patch = tissue_mask[patch_y: patch_y + patch_height, patch_x: patch_x + patch_width];
                image_patch = image[patch_y: patch_y + patch_height, patch_x: patch_x + patch_width];

                nu_ratio, nu_area, nu_peri = cal_patch_tissue(patch, tissue_patch);
                patch_area_micro = patch_width * patch_height * mpp * mpp;
                nu_area_micro = patch_area_micro * nu_ratio;

                has_tumor = get_tumor_intersect(tumor_list, tumor_label, patch_x, patch_y, patch_width, patch_height, tile_x, tile_y);

                wrtline = [caseid, img_width, img_height, mpp, mpp, patch_x+tile_x, patch_y+tile_y, patch_width, patch_height,
                           patch_area_micro, nu_area_micro, nu_ratio, nu_area, nu_peri, has_tumor];

                # For pyradiomics
                pyrad_feat_fg = pyradiomics_ins.cal_pyradiomics(image_patch, (patch > 0).astype(np.uint8));
                wrtline = wrtline + pyrad_feat_fg;
                pyrad_feat_bg = pyradiomics_ins.cal_pyradiomics(image_patch, 1-(patch > 0).astype(np.uint8));
                wrtline = wrtline + pyrad_feat_bg;

                writer.writerow(wrtline);


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

    # Read the rgb file
    org_img = skimage.io.imread(rgb_tile_path).astype(np.float);
    img = org_img / 255;  # Divide by 255 to convert to [0,1]
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

    return org_img, tissue_mask;


if __name__ == "__main__":
    csvfile  = './Bridge_files/PC_058_0_1.PC_058_0_1.2101722567_mpp_0.2464_x45056_y47104-features.csv';
    jsonfile = './Bridge_files/PC_058_0_1.PC_058_0_1.2101722567_mpp_0.2464_x45056_y47104-algmeta.json';
    svsfile = './Bridge_files/PC_058_0_1.svs';
    outfiledir = './Bridge_files/';
    outtiledir = './Bridge_files/tiles';
    outtissuedir = './Bridge_files/tiles';
    tumorfile = './Bridge_files/PC_058_0_1-tumor_region_coordinate.csv'

    # For pyradiomics
    feature_setting_file = './pyrad_features.txt'
    pyradiomics_ins = PyRadiomics_Features(feature_setting_file);

    process_tile(csvfile, jsonfile, outfiledir, svsfile, outtiledir, outtissuedir, tumorfile, pyradiomics_ins);

