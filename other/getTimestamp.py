from pymongo import MongoClient
import datetime
import sys

    
    
if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python getTimestamp.py";
    exit(); 
   
  #db_host ="quip3.bmi.stonybrook.edu"; 
  db_host = "tahsin175.informatics.stonybrook.edu";
  db_port = "27017";
  db_name = "quip";  
      
  client = MongoClient('mongodb://'+db_host+':'+db_port+'/');     
  db = client[db_name];    
  images =db.images; 
  metadata=db.metadata;
  objects = db.objects;        
    
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
         
  exit(); 
  
