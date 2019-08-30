<html>
  <head>
    <title>QC Index</title>
  </head>
  <body>
    <h1>QC Index</h1>
    <ul style="list-style-type:none;">
      {% for url in urls %}
      <li><a href="{{ url }}">{{ url }}</a></li>
      {% endfor %}
    </ul>
  </body>
</html>