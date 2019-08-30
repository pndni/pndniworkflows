<!DOCTYPE html>
<!--http://css3.bradshawenterprises.com/cfimg/-->
<!--https://www.w3schools.com/html/html_forms.asp-->
<!--https://www.w3schools.com/TAGS/ev_onsubmit.asp-->
<!--https://www.w3schools.com/jsref/dom_obj_form.asp-->
<!--https://stackoverflow.com/questions/16870876/writing-html-form-data-to-a-txt-file-without-the-use-of-a-webserver-->
<!--https://stackoverflow.com/questions/9618504/how-to-get-the-selected-radio-button-s-value#9618826-->
<!--https://stackoverflow.com/questions/833015/does-execcommand-saveas-work-in-firefox/13696029#13696029-->
<!--https://stackoverflow.com/questions/3665115/how-to-create-a-file-in-memory-for-user-to-download-but-not-through-server/18197341#18197341-->
<html>
  <head>
    <title>{{ title }}</title>
    <style>
      @keyframes fade {
        0% {opacity: 0;}
        25% {opacity: 1;}
        50% {opacity: 1;}
        75% {opacity: 0;}
        100% {opacity: 0;}
      }
      .imagebase { position: relative; }
      .first { position: relative; left: 0; }
      .second { position: absolute; left: 0;
		   animation-name: fade;
		   animation-duration: 4s;
		   animation-iteration-count: infinite;
		   animation-timing-function: linear; }
      .output { max-height: 15em; overflow: auto }
    </style>
    <script language="Javascript">
      function submitform(){
	  var outobj = {};
	  for (e of document["forms"]){
	      if (e.className == "radioform"){
		  for (r of e){
		      if (r.checked){
			  outobj[e.name] = r.value;
			  break;
		      }
		  }
	      } else if (e.className == "textform"){
		  outobj[e.name] = e[0].value
	      }
	  }
	  // this part from Matej Pokorny and mikemaccana at https://stackoverflow.com/questions/3665115/how-to-create-a-file-in-memory-for-user-to-download-but-not-through-server/18197341#18197341
	  var outel = document.createElement('a');
	  outel.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(JSON.stringify(outobj)));
	  outel.setAttribute("download", document.title.concat("_QC.json"));
	  outel.style.display = "none";
	  document.body.appendChild(outel);
	  outel.click();
	  document.body.removeChild(outel);
      }
    </script>
  </head>
  <body>
  {{ body }}
  {% if form %}
  <form onsubmit="submitform()">
    <input type="submit" value="Download QC">
  </form>
  {% endif %}
  </body>
</html>
