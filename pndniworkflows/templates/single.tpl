    <h2>{{ name }}</h2>
    <div class="imagebase">
    	 {{ svg }}
    </div>
    {% if form %}
    <form name={{ name_no_spaces }} class=radioform>
    	  <input type="radio" value="0">0 <input type="radio" value="0.25">0.25 <input type="radio" value="0.5">0.5 <input type="radio" value="0.75">0.75  <input type="radio" value="1">1 
    </form>
    <form name={{ name_no_spaces }}_notes class=textform>
    	  Notes
    	  <input type="text">
    </form>
    {% endif %}