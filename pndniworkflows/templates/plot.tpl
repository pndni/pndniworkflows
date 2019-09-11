    <h2>{{ name }}</h2>
    {% if errormessage %}
    <div class="errormessage">
    {{ errormessage }}
    </div>
    {% else %}
    <div class="description">
    Showing file
    <ul>
        <li><a href="{{ filename }}">{{ filename }}</a></li>
    </ul>
    with labels from
    <ul>
        <li><a href="{{ labelfilename }}">{{ labelfilename }}</a></li>
    </ul>
    <div class="plotbase">
    	 {{ svg }}
    </div>
    {% endif %}
    {% if form %}
    <form name={{ name_no_spaces }} class=radioform>
    	  <input type="radio" value="0">0 <input type="radio" value="0.25">0.25 <input type="radio" value="0.5">0.5 <input type="radio" value="0.75">0.75  <input type="radio" value="1">1 
    </form>
    <form name={{ name_no_space_ }}_notes class=textform>
    	  Notes
    	  <input type="text">
    </form>
    {% endif %}