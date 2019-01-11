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

 $Url = "http://quip-data:9099/services/validate_image_list/ImageList/query/findAll";
 $apiKey = $_SESSION["api_key"];
 $dataUrl = $Url . "?api_key=".$apiKey;
 $content_json = array();  
 $content_json = fetchData($dataUrl);

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
    <div id="s_search">
			<input type="text" id="search" placeholder="Search" onkeyup="search()"/>
		</div>	
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

  function search(){
  // Declare variables 
  var input, filter, table, tr, td, i;
  input = document.getElementById("search");
  filter = input.value.toUpperCase();
  table = document.getElementById("table");
  tr = table.getElementsByTagName("tr");

  // Loop through all table rows, and hide those who don't match the search query
  for (i = 0; i < tr.length; i++) {
	  var t = tr[i].getElementsByTagName("td");
	  var td = tr[i].getElementsByTagName("td")[0];
	  var key = "";
	  for(var j=0; j<t.length; j++){
		 var col = t[j].innerHTML.toUpperCase();
	   key += " ";
		 key += col;
	  }
	  
 	 if(td){
   	if(key.indexOf(filter) > -1){
		   tr[i].style.display = "";
	   } else {
		   tr[i].style.display = "none";
	   }
	 }    
  }
 }

	var newData = [];			
		for(var i in data){
			//data[i]['case_id'] = data[i]['case_id'];	
      data[i]['case_id'] = "<a href='radiomics_features.php?case_id="+ data[i]['case_id']+"'>"+ data[i]['case_id'] + "</a>"		
      delete data[i]['date_time'];
      newData.push(data[i]);    					
			//newData = data;						
			}	
		//console.log(newData);
		var table =ConvertJsonToTable(newData, 'tbl' ,null, "Download");

		$("#table").append(table);			
	</script>
	</body>
</html>