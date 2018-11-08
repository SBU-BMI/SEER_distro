import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy as np
import sys
import os
import json 
from pymongo import MongoClient


if __name__ == '__main__':
  if len(sys.argv)<1:
    print "usage:python generate_histogram.py config.json";
    exit();  
  
  local_folder="/home/bwang/patch_level";
  picture_folder = os.path.join(local_folder, 'picture'); 
  
  print " --- read config.json file ---" ;
  config_json_file = sys.argv[-1];  
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
  
  patch_level_dataset = db2.patch_level_features_run2;
  #patch_level_dataset = db2.patch_level_features;
  
  image_array=[];
  for record in patch_level_dataset.distinct("case_id"):
    #print record;
    image_array.append(record);
  #print image_array;  
  #exit();
    
  feature_array=['nucleus_area','percent_nuclear_material','grayscale_segment_mean','Hematoxylin_segment_mean'];
  
  #db.inventory.find( { $and: [ { price: { $ne: 1.99 } }, { price: { $exists: true } } ] } )

  for case_id in image_array[:]:
    for feature in feature_array[1:2]:      
      feature_value_array=[];      
      for record in patch_level_dataset.find({"case_id":case_id,"$and":[{feature:{ "$ne": "n/a" }},{feature:{ "$gte": 0.0 }}]} ,{feature:1,"_id":0}):
        feature_value=record[feature];
        feature_value_array.append(feature_value); 
      print case_id,feature;   
      #print feature_value_array;        
      n, bins, patches = plt.hist(feature_value_array,  bins=10, facecolor='#0504aa')
      #n, bins, patches = plt.hist(feature_value_array,  bins='auto', facecolor='#0504aa', alpha=0.5)
      plt.xlabel('Value')
      plt.ylabel('Counts')
      plt.title("patch level "+ feature+ ' Histogram of image '+ str(case_id))
      #Tweak spacing to prevent clipping of ylabel
      plt.subplots_adjust(left=0.15)
      #plt.show();
      file_name="patch_level_histogram_"+case_id+"_"+feature+".png";  
      graphic_file_path = os.path.join(picture_folder, file_name);
      plt.savefig(graphic_file_path);
      print "------------------------------------------";
      
      
      
  
  """  
  rng = np.random.RandomState(10)  # deterministic random data
  a = np.hstack((rng.normal(size=1000),rng.normal(loc=5, scale=2, size=1000)))
  print a
  print len(a)
  exit();
  plt.hist(a, bins=20)  # arguments are passed to np.histogram
  plt.title("Histogram with 20 bins")
  plt.show()
  """  
  """
  # example data
  mu = 100 # mean of distribution
  sigma = 15 # standard deviation of distribution
  x = mu + sigma * np.random.randn(10000) 
  num_bins = 20
  # the histogram of the data
  n, bins, patches = plt.hist(x, num_bins, normed=1, facecolor='blue', alpha=0.5) 
  # add a 'best fit' line
  y = mlab.normpdf(bins, mu, sigma)
  plt.plot(bins, y, 'r--')
  plt.xlabel('Smarts')
  plt.ylabel('Probability')
  plt.title(r'Histogram of IQ: $\mu=100$, $\sigma=15$') 
  # Tweak spacing to prevent clipping of ylabel
  plt.subplots_adjust(left=0.15)
  plt.show()
  """  
  """
  # An "interface" to matplotlib.axes.Axes.hist() method
  n, bins, patches = plt.hist(x=d, bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
  plt.grid(axis='y', alpha=0.75)
  plt.xlabel('Value')
  plt.ylabel('Frequency')
  plt.title('My Very Own Histogram')
  plt.text(23, 45, r'$\mu=15, b=3$')
  maxfreq = n.max()
  # Set a clean upper y-axis limit.
  plt.ylim(ymax=np.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)
  """   
  """
  # Generate data on commute times.
  size, scale = 1000, 10
  commutes = pd.Series(np.random.gamma(scale, size=size) ** 1.5)

  commutes.plot.hist(grid=True, bins=20, rwidth=0.9,color='#607c8e')
  plt.title('Commute Times for 1,000 Commuters')
  plt.xlabel('Counts')
  plt.ylabel('Commute Time')
  plt.grid(axis='y', alpha=0.75)
  """
  exit(); 

