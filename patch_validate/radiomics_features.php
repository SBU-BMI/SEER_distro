<?php
 function fetchData($dataUrl){
      $cSession = curl_init();
      try {
          $ch = curl_init();
          if (FALSE === $ch)
              throw new Exception('failed to initialize');
              
          curl_setopt($ch,CURLOPT_URL, $dataUrl);
          curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
          curl_setopt($ch,CURLOPT_HEADER, false);
          $content = curl_exec($ch);
          //print_r($content);
          if (FALSE === $content)
              throw new Exception(curl_error($ch), curl_errno($ch));   
      
          // ...process $content now
      } catch(Exception $e) {    
          $content = "Error";
          return $content;         
      }     
      $content_json = json_decode($content);
      return $content_json; 
  }
  
 session_start();
 require '../authenticate.php';

 $Url = "http://quip-data:9099/services/validate_image_list/RadiomicsFeatures/query/findFeatureById";
 $apiKey = $_SESSION["api_key"];
 $dataUrl = $Url . "?api_key=".$apiKey;
 $case_id=$_GET["case_id"];
 $dataUrl=$dataUrl . "&case_id=". $case_id;
 $content_json = array();  
 //print_r($dataUrl);
 $content_json = fetchData($dataUrl);
 //print_r($content_json); 
 $result = array();
 if(!empty($content_json) and $content_json!='Error'){
    foreach ($content_json as $record) {
       $a_record = (array)$record;
       array_push($result,$a_record);
    }
 }
?>

<html>
	<head>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" type="text/css"/>
        <link rel="stylesheet" href="style.css" type="text/css"/>
	      <title>SEER VTR</title>
        <script src="https://code.jquery.com/jquery-2.2.4.min.js" integrity="sha256-BbhdlvQf/xTY9gja0Dq3HiwQF8LaCRTXxZKRutelT44=" crossorigin="anonymous"></script>
	      <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.11.0/d3.min.js"> </script>
</head>
	<body>
		<h1 id="heading">SEER VTR Radiomics Feature Image List</h1>	    
		<div id="table">
	</div>
		
<script type="text/javascript" src="json-to-table.js"></script>

<script type="text/javascript"> 
  var data = <?php echo json_encode($result); ?>;
			
  function containsObject(obj, list) {
    var i;
    for (i = 0; i < list.length; i++) {
        if (list[i] === obj) {
            return true;
        }
    }

    return false;
  }  

	var newData = [];			
	for(var i in data){			  
      //move patch center to the windoe screen center
      x= parseInt(data[i]['patch_x']) + parseInt(data[i]['patch_width'])/2;
      y= parseInt(data[i]['patch_y']) + parseInt(data[i]['patch_height'])/2;  
      patch_location="&x=" + x +"&y=" + y +"&patch_width=" + data[i]['patch_width']+"&patch_height=" + data[i]['patch_height']+"&image_width=" + data[i]['image_width']+"&image_height=" + data[i]['image_height']; 
      data[i]['case id'] = "<a href='http://tahsin175.informatics.stonybrook.edu/camicroscope/radiomics_patch.php?tissueId="+ data[i]['case_id']+ patch_location+"'>"+ data[i]['case_id']  + "</a>"; 
      data[i]['patch x']=data[i]['patch_x'];
      data[i]['patch y'] =data[i]['patch_y'];
      delete data[i]['case_id'];
      delete data[i]['patch_x'];
      delete data[i]['patch_y'];
      delete data[i]['image_width'];
      delete data[i]['image_height'];
      delete data[i]['patch_width'];
      delete data[i]['patch_height']; 
         
      data[i]['nuclei ratio']= data[i]['nuclei_ratio'].toFixed(2);  
      data[i]['nuclei average area']= data[i]['nuclei_average_area'].toFixed(2);       
      data[i]['nuclei average perimeter']= data[i]['nuclei_average_perimeter'].toFixed(2);      
      data[i]['nuclei area micro']= data[i]['nuclei_area_micro'].toFixed(2);
      data[i]['patch area micro']= data[i]['patch_area_micro'].toFixed(2); 
      
      delete data[i]['nuclei_ratio'];
      delete data[i]['nuclei_average_area'];
      delete data[i]['nuclei_average_perimeter'];
      delete data[i]['nuclei_area_micro'];
      delete data[i]['patch_area_micro'];                  
      newData.push(data[i]); 									
			}	
  //console.log(newData);
  var table =ConvertJsonToTable(newData, 'tbl' ,null, "Download");
	$("#table").append(table);			
</script>

	</body>
</html>