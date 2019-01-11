#!/bin/bash

STORAGE_FOLDER="/home/feiqiao/quip2/"

docker network create quip_nw

IMAGES_DIR=$(echo $STORAGE_FOLDER/img)
DATABASE_DIR=$(echo $STORAGE_FOLDER/data)

#mkdir -p $IMAGES_DIR 
#mkdir -p $DATABASE_DIR

VIEWER_PORT=80
VIEWER_PORT2=8080
IMAGELOADER_PORT=6002
FINDAPI_PORT=3000

data_host="http://quip-data:9099"
mongo_host="quip-data"
mongo_port=27017

# pull docker images from hub.docker.com to quip3 server
docker pull bridge2014/quip_viewer_quip3:latest
docker pull bridge2014/quip_data_quip3:latest
docker pull bridge2014/quip_composite_quip3:latest
docker pull bridge2014/quip_findapi_quip3:latest
docker pull bridge2014/quip_dynamic_quip3:latest
docker pull bridge2014/quip_jobs_quip3:latest
docker pull bridge2014/quip_oss_quip3:latest
docker pull bridge2014/quip_loader_quip3:latest


quip_viewer="bridge2014/quip_viewer_quip3:latest"
quip_data="bridge2014/quip_data_quip3:latest"
quip_composite="bridge2014/quip_composite_quip3:latest"
quip_findapi="bridge2014/quip_findapi_quip3:latest"
quip_dynamic="bridge2014/quip_dynamic_quip3:latest"
quip_jobs="bridge2014/quip_jobs_quip3:latest"
quip_oss="bridge2014/quip_oss_quip3:latest"
quip_loader="bridge2014/quip_loader_quip3:latest"

#\cp -rf configs $STORAGE_FOLDER/.
CONFIGS_DIR=$(echo $STORAGE_FOLDER/configs)

## Run data container
data_container=$(docker run --name quip-data --net=quip_nw --restart unless-stopped -itd \
  -p 27017:27017 \
 	-v quip_bindaas:/root/bindaas \
	-v $IMAGES_DIR:/data/images \
	-v $DATABASE_DIR:/var/lib/mongodb \
	$quip_data)
echo "Started data container: " $data_container

echo "This might take 30 seconds"
sleep 15

## Run loader container
loader_container=$(docker run --name quip-loader --net=quip_nw --restart unless-stopped -itd \
	-v $IMAGES_DIR:/data/images \
	-e "mongo_host=$(echo $mongo_host)" \
	-e "mongo_port=$(echo $mongo_port)" \
	-e "dataloader_host=$(echo $data_host)" \
	-e "annotations_host=$(echo $data_host)" \
	$quip_loader)
echo "Started loader container: " $loader_container

## Run viewer container
viewer_container=$(docker run --name=quip-viewer --net=quip_nw  --restart unless-stopped -itd \
	-p $VIEWER_PORT:80 \
 	-p $VIEWER_PORT2:8080 \
	-v $IMAGES_DIR:/data/images \
	-v $STORAGE_FOLDER/configs/security:/var/www/html/config \
  -v $STORAGE_FOLDER/configs/security:/var/www/html2/config \
  -v $STORAGE_FOLDER/composite_results:/var/www/html2/composite_results \
  -v $STORAGE_FOLDER/cluster_indices:/var/www/html/cluster_indices \
	$quip_viewer)
echo "Started viewer container: " $viewer_container


## Run oss-lite container
oss_container=$(docker run --name quip-oss --net=quip_nw --restart unless-stopped -itd \
	-v $IMAGES_DIR:/data/images \
	$quip_oss)
echo "Started oss-lite container: " $oss_container

## Run job orders service container
jobs_container=$(docker run --name quip-jobs --net=quip_nw --restart unless-stopped -itd \
  $quip_jobs) 
echo "Started job orders container: " $jobs_container

## Run dynamic services container
sed 's/\@QUIP_JOBS/\"quip-jobs\"/g' $CONFIGS_DIR/config_temp.json > $CONFIGS_DIR/config_tmp.json
sed 's/\@QUIP_OSS/\"quip-oss:5000\"/g' $CONFIGS_DIR/config_tmp.json > $CONFIGS_DIR/config.json
sed 's/\@QUIP_DATA/\"quip-data\"/g' $CONFIGS_DIR/config.json > $CONFIGS_DIR/config_tmp.json
sed 's/\@QUIP_LOADER/\"quip-loader\"/g' $CONFIGS_DIR/config_tmp.json > $CONFIGS_DIR/config.json
dynamic_container=$(docker run --name quip-dynamic --net=quip_nw --restart unless-stopped -itd \
	-v $CONFIGS_DIR:/tmp/DynamicServices/configs \
	$quip_dynamic)

echo "Started dynamic services container: " $dynamic_container

# Run findapi service container
findapi_container=$(docker run --name quip-findapi --net=quip_nw --restart unless-stopped -itd \
	-e "MONHOST=$(echo $mongo_host)" \
	-e "MONPORT=$(echo $mongo_port)" \
	$quip_findapi)
echo "Started findapi service container: " $findapi_container

# Run composite dataset generating container
composite_container=$(docker run --name quip-composite --net=quip_nw --restart unless-stopped -itd \
 $quip_composite) 
echo "Started composite dataset generating container: " $composite_container
