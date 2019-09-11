    <h2>{{ name }}</h2>
    {% for crash in crashes %}
       <div class="description">
       From crashfile <a href="{{ crash.crashfile }}">{{ crash.crashfile }}</a>
       </div>
       <div class="crash">
       <dl>
           <dt>Node Name</dt><dd>{{ crash.nodename }}</dd>
           <dt>Node Full Name</dt><dd>{{ crash.nodefullname }}</dd>
           <dt>Interface</dt><dd>{{ crash.interface }}</dd>
           <dt>Traceback</dt><dd><samp>{{ crash.traceback }}</samp></dd>
       </dl>
       </div>
   {% else %}
       <div class="success">
       No crash files found!
       </div>
   {% endfor %}
	   