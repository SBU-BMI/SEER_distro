    <?php 
    require '../authenticate.php';
    $config = require 'api/Configuration/config.php';
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>[caMicroscope OSD][Subject: <?php echo json_encode($_GET['tissueId']); ?>][User: <?php echo $_SESSION["name"]; ?>]</title>

        <!-- Tooltip dependencies -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
        <link rel="stylesheet" type="text/css" media="all" href="css/annotools.css" />        
        <link rel="stylesheet" type="text/css" media="all" href="css/simplemodal.css" />
        <link rel="stylesheet" type="text/css" media="all" href="css/ui.fancytree.min.css" />
        
        <script src="https://code.jquery.com/jquery-3.2.1.min.js"></script>
	      <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.11.0/d3.min.js"></script>
        <!--JSON Form dependencies-->
        <script type="application/javascript" src="js/dependencies/underscore.js"></script>
        <script>
          console.log("underscore:");
          console.log(_);
        </script>
        
        <script type="text/javascript" src="js/dependencies/jsonform.js"></script>
        <script type="text/javascript" src="js/dependencies/jsv.js"></script>
        <!--End JSON Form dependencies -->        
        <script src="/js/config.js"></script>

        <script src="js/openseadragon/openseadragon-bin-1.0.0/openseadragon.js"></script>
        <script src="js/openseadragon/openseadragon-imaginghelper.min.js"></script>
        <script src="js/openseadragon/openseadragon-scalebar.js"></script>
        <script src="js/openseadragon/openseadragonzoomlevels.js"></script>
        <script type="text/javascript" src="js/mootools/mootools-core-1.4.5-full-nocompat-yc.js"></script>
        <script type="text/javascript" src="js/mootools/mootools-more-1.4.0.1-compressed.js"></script>
        <script src="js/annotationtools/annotools-openseajax-handler.js"></script>
        <script src="js/imagemetadatatools/osdImageMetadata.js"></script>
        <script src="js/annotationtools/ToolBar.js"></script>
        <script src="js/annotationtools/AnnotationStore.js"></script>
        <script src="js/annotationtools/osdAnnotationTools.js"></script>
        <script src="js/annotationtools/geoJSONHandler.js"></script>
        <script src="js/dependencies/MD5.js"></script>
        <script src="https://code.jquery.com/ui/1.11.2/jquery-ui.min.js" type="text/javascript"></script>     

        <!--Filtering Tools-->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/camanjs/4.1.2/caman.full.js"></script>
        <script src="js/filteringtools/openseadragon-filtering.js"></script>
        <script src="js/filteringtools/spinner-slider.js"></script>
        <script src="js/filteringtools/spinner.js"></script>
        <script src="js/filteringtools/FilterTools.js"></script>
        <!--End Filtering Tools-->    
        
        <script src="js/dependencies/jquery.fancytree-all.min.js"></script>
        <script src="js/dependencies/simplemodal.js"></script>
        <style type="text/css">
            .openseadragon
            {
                height: 100%;
                min-height: 100%;
                width: 100%;
                position: absolute;
                top: 0;
                left: 0;
                margin: 0;
                padding: 0;
                background-color: #E8E8E8;
                border: 1px solid black;
                color: white;
            }

        .navWindow

        {
            position: absolute;
                z-index: 10001;
                right: 0;
                bottom: 0;
                border: 1px solid yellow;
        }
        </style>
    </head>

    <body> 

        <div id="container">                    
            <div id="tool"></div>
            <div id="panel"></div>
            <div id="bookmarkURLDiv"></div>
            <div id="algosel">
                <div id="tree"></div>
            </div>

            <div class="demoarea">
                <div id="viewer" class="openseadragon"></div>
            </div>
            <div id="navigator"></div>
        </div>

        <script type="text/javascript">
          var tissueId = <?php echo json_encode($_GET['tissueId']); ?>;
	        var displayId = tissueId;
          var user_email = "<?php echo $_SESSION["email"]; ?>";  
          console.log("user_email :" + user_email);

          d3.csv("../table/data.csv", function(data){
		        console.log(data);
		        for(var i in data){
		     	    var d = data[i];
			        var id = (d['DxSlide1_FileName']);
			        if(tissueId == id){
				        console.log("here");
				        console.log(d);
				        displayId = d['Reformatted_DxSlide1_BarcodeID'];		
			        }
		        }
  	      })

          $.noConflict();

          var annotool = null;
          var imagedata = new OSDImageMetaData({imageId:tissueId});         
          var MPP = imagedata.metaData[0];
          var fileLocation = imagedata.metaData[1];
          jQuery("#bookmarkURLDiv").hide();
         
          var viewer = new OpenSeadragon.Viewer({ 
                id: "viewer", 
                prefixUrl: "images/",
                showNavigator:  true,
                navigatorPosition:   "BOTTOM_RIGHT",
                //navigatorId: "navigator",
                zoomPerClick: 2,
                animationTime: 0.75,
                maxZoomPixelRatio: 2,
                visibilityRatio: 1,
                constrainDuringPan: true
                //zoomPerScroll: 1
          });
            //console.log(viewer.navigator);
           // var zoomLevels = viewer.zoomLevels({
           // levels:[0.001, 0.01, 0.2, 0.1,  1]
           // });
            
            viewer.addHandler("open", addOverlays);
            viewer.clearControls();
            viewer.open("<?php print_r($config['fastcgi_server']); ?>?DeepZoom=" + fileLocation);
            var imagingHelper = new OpenSeadragonImaging.ImagingHelper({viewer: viewer});
            imagingHelper.setMaxZoom(1);            
            //console.log(this.MPP);
            viewer.scalebar({
              type: OpenSeadragon.ScalebarType.MAP,
              pixelsPerMeter: (1/(parseFloat(this.MPP["mpp-x"])*0.000001)),
              xOffset: 5,
              yOffset: 10,
              stayInsideImage: true,
              color: "rgb(150,150,150)",
              fontColor: "rgb(100,100,100)",
              backgroundColor: "rgba(255,255,255,0.5)",
              barThickness: 2
            });
          
          //showPatchFeatures();

    //console.log(viewer);

    function isAnnotationActive() {
        this.isOpera = (!!window.opr && !!opr.addons) || navigator.userAgent.indexOf(' OPR/') >= 0;
        // console.log("isOpera", this.isOpera);
        this.isFirefox = typeof InstallTrigger !== 'undefined';
        // console.log("isFirefox", this.isFirefox);
        this.isSafari = ((navigator.userAgent.toLowerCase().indexOf('safari') > -1) && !(navigator.userAgent.toLowerCase().indexOf('chrome') > -1) && (navigator.appName == "Netscape"));
        // console.log("isSafari", this.isSafari);
        this.isChrome = !!window.chrome && !!window.chrome.webstore;
        // console.log("isChrome", this.isChrome);
        this.isIE = /*@cc_on!@*/false || !!document.documentMode;
        // console.log("isIE", this.isIE);
        this.annotationActive = !( this.isIE || this.isOpera);
        // console.log("annotationActive", this.annotationActive);
        return this.annotationActive;
    }
    
    function showPatchFeatures(){
      var container = document.getElementsByClassName("openseadragon-canvas")[0];       
      var viewer_width = parseInt(container.offsetWidth)
      var viewer_height = parseInt(container.offsetHeight)
      var x_new=viewer_width/2;
      var y_new=viewer_height/2;
      
      //(x,y) is cnter odf patch
      //var x = <?php echo json_encode($_GET['x']); ?>;
      //var y = <?php echo json_encode($_GET['y']); ?>;
      var patch_width   = <?php echo json_encode($_GET['patch_width']); ?>;
      var patch_height = <?php echo json_encode($_GET['patch_height']); ?>;  
      var image_width = <?php echo json_encode($_GET['image_width']); ?>;
      var image_height = <?php echo json_encode($_GET['image_height']); ?>;
      var x1=parseInt(x_new) - parseInt(patch_width)/2;
      var y1=parseInt(y_new) - parseInt(patch_height)/2;
      var x2=x1+parseInt(patch_width);
      var y2=y1+parseInt(patch_height);
            
      var nativepoints = [];  
      /*    
      nativepoints.push([x1/parseInt(image_width), y1/parseInt(image_height)]);      
      nativepoints.push([x2/parseInt(image_width), y1/parseInt(image_height)]);
      nativepoints.push([x2/parseInt(image_width), y2/parseInt(image_height)]);
      nativepoints.push([x1/parseInt(image_width), y2/parseInt(image_height)]);
      nativepoints.push([x1/parseInt(image_width), y1/parseInt(image_height)]);      
      */
      nativepoints.push([x1,y1]);      
      nativepoints.push([x2,y1]);
      nativepoints.push([x2,y2]);
      nativepoints.push([x1,y2]);
      nativepoints.push([x1,y1]);
      
      /* Why is there an ellipse in the center? */
      var svgHtml = '<svg xmlns="http://www.w3.org/2000/svg" width="' + viewer_width + 'px" height="' + viewer_height + 'px" version="1.1" id="markups">'
      
      svgHtml += '<g id="groupcenter"/>'  
      
      
      /*    
      svgHtml += '<g id="origin">'
      var origin = viewer.viewport.pixelFromPoint(new OpenSeadragon.Point(.5, .5))
      svgHtml += '<ellipse id="originpt" cx="' + origin.x + '" cy="' + origin.y + '" rx="' + 4 + '" ry="' + 4 + '" style="display: none"/>'
      svgHtml += '</g>'
      */
      svgHtml += '<g id="viewport" transform="translate(0,0)">'      
      var id = '';  
               
      svgHtml += '<polygon  class="" id="' + id + '" points="'                  
      for (var k = 0; k < nativepoints.length; k++) {        
        var polyPixelX = nativepoints[k][0]
        var polyPixelY = nativepoints[k][1]       
        svgHtml += polyPixelX + ',' + polyPixelY + ' '        
      }         
       
      //svgHtml += '<polygon  class="" id="' + id + '" points="400,400 900,400 900,900 400,900 400,400 '   
       
      svgHtml += '" style="stroke:green; stroke-width:2.0; fill-opacity:0.0"/>';
         
      this.svg = new Element('div', {
        styles: {
          position: 'absolute',
          left: 0,
          top: 0,
          width: '100%',
          height: '100%'
        },
        html: svgHtml
      }).inject(container)      
      
    }

    function addOverlays() {
        var annotationHandler = new AnnotoolsOpenSeadragonHandler(viewer, {});
        
        annotool= new annotools({
                canvas:'openseadragon-canvas',
                iid: tissueId, 
		            displayId: tissueId,
                user_email: user_email,
                viewer: viewer,
                annotationHandler: annotationHandler,
                mpp:MPP
            });
        filteringtools = new FilterTools();
        //console.log(tissueId);
        var toolBar = new ToolBar('tool', {
                left:'0px',
                top:'0px',
                height: '48px',
                width: '100%',
                iid: tissueId,
                user_email: user_email,
                annotool: annotool,
                FilterTools: filteringtools
        });
        annotool.toolBar = toolBar;
        toolBar.createButtons();

        var index = user_email.indexOf("@");
        var user= user_email.substring(0,index);		
        annotool.user = user;

        // For the bootstrap tooltip
        // jQuery('[data-toggle="tooltip"]').tooltip();
        // commented out, working on style
        
        //var panel = new panel();
        jQuery("#panel").hide();
        /*Pan and zoom to point*/
        var bound_x = <?php echo json_encode($_GET['x']); ?>;
        var bound_y = <?php echo json_encode($_GET['y']); ?>;
        var zoom = <?php echo json_encode($_GET['zoom']); ?> || viewer.viewport.getMaxZoom();
        zoom=Number(zoom); // convert string to number if zoom is string         

        var stateID = <?php echo json_encode($_GET['stateID']); ?>;

        //Check if loading from saved state
        if(stateID){
            //fetch state from firebase
            jQuery.get("https://test-8f679.firebaseio.com/camicroscopeStates/"+stateID+".json?auth=kweMPSAo4guxUXUodU0udYFhC27yp59XdTEkTSJ4", function(data){

            var savedFilters = data.state.filters;
            var viewport = data.state.viewport;
            var pan = data.state.pan;
            var zoom = data.state.zoom || viewer.viewport.getMaxZoom();

            //pan and zoom have preference over viewport
            if (pan && zoom) {
                viewer.viewport.panTo(pan);
                viewer.viewport.zoomTo(zoom);
            
            } else {
                if(viewport) {
                    console.log("here");
                    var bounds = new OpenSeadragon.Rect(viewport.x, viewport.y, viewport.width, viewport.height);
                    viewer.viewport.fitBounds(bounds, true);
                }
            }
            // check if there are savedFilters
            if (savedFilters) {
              filteringtools.showFilterControls();

              for(var i=0; i<savedFilters.length; i++){                    

                    var f = savedFilters[i];
                    var filterName = f.name;

                    jQuery("#"+filterName+"_add").click();
                    if(filterName == "SobelEdge"){
                         console.log("sobel");
                    }else {
                        jQuery("#control"+filterName).val(1*f.value);
                        jQuery("#control"+filterName+"Num").val(1*f.value);
                
                    }
                }
            }
            filteringtools.updateFilters();
        
        });
        }

        if(bound_x && bound_y){
            var ipt = new OpenSeadragon.Point(+bound_x, +bound_y);
            var vpt = viewer.viewport.imageToViewportCoordinates(ipt);
            viewer.viewport.panTo(vpt);
            viewer.viewport.zoomTo(zoom);
            //showPatchFeatures();
        } else {
            //console.log("bounds not specified");
        }
    }

      if (!String.prototype.format) {
        String.prototype.format = function() {
            var args = arguments;
            return this.replace(/{(\d+)}/g, function(match, number) { 
            return typeof args[number] != 'undefined'
                ? args[number]
                : match
            ;
            });
        };
      }    
   
   //showPatchFeatures();
   //alert("hi!");
  </script>

<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-46271588-1', 'auto');
  ga('send', 'pageview');

   //window.onload =showPatchFeatures();
</script>



</body>
</html>

