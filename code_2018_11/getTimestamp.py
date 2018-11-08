from pymongo import MongoClient
import datetime
import sys

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python getTimestamp.py";
    exit(); 
   
  db_host ="quip3.bmi.stonybrook.edu"; 
  #db_host = "tahsin175.informatics.stonybrook.edu";
  db_port = "27017";
  db_name = "quip"; 
  db_name2 = "quip_comp"; 
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;
  image_attributes =db.image_attributes;        

  db2 = client[db_name2];    
  images2 =db2.images;
  
  """    
  for image_record in images.find({}):                                                      
    timestamp = image_record['timestamp']; 
    _id= image_record['_id'] ;     
    fmt = "%Y-%m-%d %H:%M:%S"
    # local time
    t = datetime.datetime.fromtimestamp(timestamp);    
    loading_date_time = t.strftime(fmt);
    print _id, loading_date_time;     
    
    images.update_one(
        {"_id": _id},
        {
         "$set": {
                   "loading_date_time":loading_date_time
                 }
        }
    );
  """   
  
  #add loading_date_time to image_attributes collection
  """
  for attribute_record in image_attributes.find({}):
    _id1=attribute_record['_id'];
    Registry=attribute_record['Registry'];
    DxSlide1_FileName=attribute_record['DxSlide1_FileName'];
    Reformatted_DxSlide1_BarcodeID=attribute_record['Reformatted_DxSlide1_BarcodeID'];
     
    if(Registry=="Iowa" or Registry== "Connecticut"):
      case_id =DxSlide1_FileName
    else:
      case_id =Reformatted_DxSlide1_BarcodeID;
    
    #print _id1,case_id;
   
    for image_record in images.find({"case_id":case_id}).limit(1):
      loading_date_time=image_record['loading_date_time'];
      print _id1,case_id,loading_date_time;      
      
      image_attributes.update_one(
        {"_id": _id1},
        {
         "$set": {
                   "loading_date_time":loading_date_time
                 }
        }
      );
  """
  
  comp_image_list =['17039922','17039789','17039920','17039897','17039875','17039876','17039871','17039872','17044732','17039787','17039788','17043254','17044738','17039823','17039824','17039895','17039825','17039826','17039833','17039861','17039877','17039878','17039891','17039892','17039889','17039890','17039885','17039873','17039880','17039869','17039870','17039840','17039827','17039828','17039836','17039829','17039830','17039841','17039842','17043436','17043484','17039831','17039832','17039843','17039844','BC_056_0_1','BC_057_0_1','BC_057_0_2','BC_059_0_2','BC_060_1_1','BC_060_1_2','BC_061_0_1','BC_061_0_2','BC_062_0_1','BC_062_0_2','BC_065_0_1','BC_065_0_2','BC_066_1_1','BC_066_1_2','BC_067_0_1','BC_067_0_2','BC_068_0_1','BC_069_0_1','BC_070_0_1','BC_070_0_2','BC_096_1_1','BC_184_1_1','BC_184_1_2','BC_201_1_1','BC_201_1_2','BC_264_1_1','BC_277_2_1','BC_277_2_2','BC_346_1_1','BC_346_1_2','BC_378_1_1','BC_388_1_1','BC_388_1_2','BC_514_1_1','BC_519_1_1','BC_519_1_2','BC_527_1_1','17032555','17032556','17032557','17032558','17032559','17033361','17032560','17032561','17032562','17032563','17032564','17033080','17033042','17032565','17035672','17032597','17033044','17033045','17033079','17035673','17033046','17033047','17033048','17035674','17032566','17032567','17032568','17032569','17032570','17032571','17033362','17032596','17033050','17032572','17035679','17033051','17032573','17033052','17033772','17033773','17033040','17032574','17032575','17032576','17033055','17033057','17032577','17032578','17033056','17033058','17032579','17033059','17032580','17032581','17032582','17032583','17032584','17032585','17032586','17032587','17032595','17032588','17033060','17032589','17032590','17032591','17033061','17035678','17032592','17033063','17033062','17033064','17032593','17033065','17033081','17032594','17039925','17039813','17039814','17039858','17039910','17039816','17039818','17039859','17039860','17039801','17039806','17039807','17039808','17039809','17039810','17039811','17039812','17039853','17039883','17039884','17039887','17039888','17039917','17039819','17039821','17039850','17039894','17039914','17039863','17039926','17039845','17039851','17039852','17039865','17039866','17039902','17039848','17039904','PC_052_0_1','PC_054_0_1','PC_054_1_1','PC_054_1_2','PC_055_0_1','PC_057_0_1','PC_058_0_1','PC_058_1_1','PC_058_1_2','PC_058_2_1','PC_061_0_1','PC_061_0_2','PC_062_0_1','PC_063_0_1','PC_064_0_1','PC_066_0_1','PC_067_0_1','PC_067_2_1','PC_136_1_1','PC_191_2_1','PC_227_2_1','17032547','17032548','17032549','17033066','17035671','17033067','17032550','17033068','17033069','17033070','17033071','17033072','17032551','17033073','17035676','17033074','17032599','17032553','17033075','17033076','17033077','17035677','17033078','17039927', '17039924', '17039879', '17039862', '17039901', '17039921', '17039817','17039794', '17039802', '17039805', '17039820', '17039791', '17039835', '17039893', '17043251','17043259', '17039796', '17039790', '17043249', '17039815', '17039792','17039868', '17044735', '17039916', '17039798', '17039799', '17039905','17043485','17039838', '17039855', '17039919', '17039797', '17039856', '17044733', '17043250','17039846', '17039795', '17043366', '17039793', '17044737','PC_050_0_1', 'PC_051_0_1', '17044731', '17039804', '17039915', '17039918', '17039923', '17039864','17039822', '17039847', '17039839', '17043255', '17039803', '17039900', '17043252', '17039882', '17043347', '17039834', '17043253','17044734', '17039857', '17039909', '17039886','17039849', '17039908', '17039854', '17039837', '17039800', '17039874','17039906','17039903','17039907','BC_268_1_1','17043486','17044736','17039911', '17039899','17039881','17039896','17040280','17040278','17040241','17040384','17040283','17040242','17040279','17040238','17040258','17040239','BC_063_0_1','17040259','17040245','17040257','17040237','BC_063_0_2','17042092','17040253','17042095','17040246','17040282','PC_065_0_1','17040281','PC_065_0_2','17040285','17042094'] ;
  print len(comp_image_list);
  
  case_id_list=[];
  for attribute_record in image_attributes.find({}):    
    Registry=attribute_record['Registry'];
    DxSlide1_FileName=attribute_record['DxSlide1_FileName'];
    Reformatted_DxSlide1_BarcodeID=attribute_record['Reformatted_DxSlide1_BarcodeID'];
     
    if(Registry=="Iowa" or Registry== "Connecticut"):
      case_id =DxSlide1_FileName
    else:
      case_id =Reformatted_DxSlide1_BarcodeID;
    case_id_list.append(case_id);
    
  print len(case_id_list);
  
  index=0;
  for case_id in images2.distinct("case_id"):  
    index+=1;  
    if case_id in case_id_list:
      #print str(case_id)+"this case_id is in image list.";
      print "--";
    else:
      print str(case_id)+"this case_id is NOT in case_id_list." ;
  
  print index;  
  
  print "===================================";
  for case_id in  case_id_list:
    if case_id in comp_image_list: 
      #print "--"; 
      continue;
    else:
      print str(case_id)+"   this case_id is NOT in comp_image_list." ;  
      
      
  """        
  for case_id in images2.distinct("case_id"):    
    if case_id in comp_image_list:
      #print str(case_id)+"this case_id is in image list.";
      print "--";
    else:
      print str(case_id)+"this case_id is NOT in image list." ;    
  """                
  exit(); 
  