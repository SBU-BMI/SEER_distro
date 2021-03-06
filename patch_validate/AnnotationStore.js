var AnnotationStore = function (iid) {
  this.annotations = []
  this.iid = iid
  this.cacheBounds = {
    x1: 100,
    y1: -1,
    x2: 1,
    y2: 2
  }
}

AnnotationStore.prototype.getAnnotations = function (x1, y1, x2, y2, footprint, algorithms, boundX1, boundY1, boundX2, boundY2, callback) {
  var self = this

  if (Math.round(footprint) != 16) {
    self.setCacheBounds(100, -1, 1, 2)

    var annotations = this.fetchAnnotations(x1, y1, x2, y2, footprint, algorithms, callback)
  } else {
    if (this.cacheBounds.x1 > x1 || this.cacheBounds.y1 > y1 || this.cacheBounds.x2 < x2 || this.cacheBounds.y2 < y2) {
      if (this.cacheBounds.x1 > x1) {
        console.log('x lower bound')
      }
      if (this.cacheBounds.y1 > y1) {
        console.log('y lower bound')
      }
      if (this.cacheBounds.x2 < x2) {
        console.log('x upper bound')
      }
      if (this.cacheBounds.y2 < y2) {
        console.log('y upper bound')
      }

      var x_1 = x1 - boundX1
      var y_1 = y1 - boundY1
      var x_2 = x2 + boundX2
      var y_2 = y2 + boundY2
      if (x_1 < 0)
        x_1 = 0
      if (y_1 < 0)
        y_1 = 0

      self.setCacheBounds(x_1, y_1, x_2, y_2)
      // console.log("fetching.........")
      console.log('Clearing and fetching cache')
      var annotations = this.fetchAnnotations(x_1, y_1, x_2, y_2, footprint, algorithms, callback)
    } else {
      console.log('from cache')
      callback(self.annotations)
    }
  }
}

AnnotationStore.prototype.setCacheBounds = function (x1, y1, x2, y2) {
  this.cacheBounds.x1 = x1
  this.cacheBounds.x2 = x2
  this.cacheBounds.y1 = y1
  this.cacheBounds.y2 = y2
}

AnnotationStore.prototype.getCacheBounds = function () {
  return this.cacheBounds
}

AnnotationStore.prototype.fetchAnnotations = function (x1, y1, x2, y2, footprint, algorithms, callback) {
  var self = this
  if (footprint == 16)
    console.log(footprint)
  var midX = x2
  var midY = y2
  /*
  var algorithms_urlparam = JSON.stringify(algorithms)
  algorithms_urlparam = algorithms_urlparam.replace('[', '%5B')
  algorithms_urlparam = algorithms_urlparam.replace(']', '%5D')
  algorithms_urlparam = algorithms_urlparam.replace(/"/g, '%22')

  //dispaly composite_input annotation while in low scale viewport
   var isCompositeAnnotationOnly= true;
   var algorithm_number = algorithms.length;
   if (algorithm_number >0) {
 	for (i=0; i< algorithm_number; i++){
		var index=algorithms[i].indexOf("composite_input");	
		 //not find composite annotation
		if(index == -1){
	  	 isCompositeAnnotationOnly= false;}
	}
   }	
   if(algorithm_number >0 && isCompositeAnnotationOnly)
	footprint = 1 ;  //find composite_input annotation only
	
  var url1 = 'api/Data/getMultipleAnnots.php?iid=' + self.iid + '&x=' + x1 + '&y=' + y1 + '&x1=' + midX + '&y1=' + midY + '&footprint=' + footprint + '&algorithms=' + algorithms_urlparam
  console.log(url1)
  */
  
  //dispaly composite_input annotation while in low scale viewport
	var isCompositeAnnotationOnly= true;
	var isNonCompositeAnnotationOnly=true;
	var algorithms_computer= [];
	var algorithms_human = [];
	
	var algorithm_number = algorithms.length;
	
	if (algorithm_number >0) {
		for (i=0; i< algorithm_number; i++){
			var index=algorithms[i].indexOf("composite_input");	
			 //not find composite annotation
			if(index == -1){
		  	 isCompositeAnnotationOnly= false;
			 algorithms_computer.push(algorithms[i]);  
			 }
			 
			if(index != -1){
		  	 isNonCompositeAnnotationOnly= false;
			 algorithms_human.push(algorithms[i]); 
			 } 
		}
	}
	
	if(algorithm_number >0 && isCompositeAnnotationOnly)
		footprint = 1 ;  //find composite_input annotation only 	
	
	if( algorithm_number == 1  && algorithms[0].indexOf("patch_") !=-1  )
          footprint = 1 ;// find patch_location or patch_segment entry

    if( algorithm_number == 2  && algorithms[0].indexOf("patch_") !=-1 && algorithms[1].indexOf("patch_") !=-1  )
          footprint = 1 ;// find patch_location or patch_segment entry

	
    var algorithms_urlparam = JSON.stringify(algorithms);		
    algorithms_urlparam = algorithms_urlparam.replace("[", "%5B");
    algorithms_urlparam = algorithms_urlparam.replace("]", "%5D");
    algorithms_urlparam = algorithms_urlparam.replace(/"/g, "%22");
	
	var algorithms_urlparam_computer = JSON.stringify(algorithms_computer);		
    algorithms_urlparam_computer = algorithms_urlparam_computer.replace("[", "%5B");
    algorithms_urlparam_computer = algorithms_urlparam_computer.replace("]", "%5D");
    algorithms_urlparam_computer = algorithms_urlparam_computer.replace(/"/g, "%22");
	
	var algorithms_urlparam_human = JSON.stringify(algorithms_human);		
    algorithms_urlparam_human = algorithms_urlparam_human.replace("[", "%5B");
    algorithms_urlparam_human = algorithms_urlparam_human.replace("]", "%5D");
    algorithms_urlparam_human = algorithms_urlparam_human.replace(/"/g, "%22");
	
    //console.log(algorithms_urlparam);
    var url1;
	
    //if(isCompositeAnnotationOnly || isNonCompositeAnnotationOnly) {
       //url1 = "api/Data/getMultipleAnnotsClone.php?iid="+  self.iid +"&x=" + x1+ "&y=" + y1 + "&x1=" + midX + "&y1=" + midY + "&footprint="+ footprint + "&algorithms=" + algorithms_urlparam;
  	//}else {
	  url1 = "api/Data/getMultipleAnnotationsNew.php?iid="+  self.iid +"&x=" + x1+ "&y=" + y1 + "&x1=" + midX + "&y1=" + midY + "&footprint="+ footprint + "&algorithms_computer=" + algorithms_urlparam_computer+ "&algorithms_human=" + algorithms_urlparam_human;	
	//}
	
   //console.log(url1);  
	
  jQuery.get(url1, function (data) {  
    //console.log(data);
    var d = {};
    try{
	
    	d = JSON.parse(data);
    } catch(e){
	d = []; 
    }
    self.annotations = d
    if (callback)
      callback(d)
  })
}
