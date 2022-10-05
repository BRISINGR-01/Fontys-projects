# Fontys-projects
All the project worthy of showing that I have build during my time as a student at [Fontys](https://fontys.edu/Bachelors-masters/Bachelors/Information-Communication-Technology-Eindhoven.htm)

# Greenhouse
A website for displaying the data for a greenhouse:
## Info
  - python backend - Flask framework
  - jinja/html and js frontend - Chart.js library
  - Arduino UNO for measuring temperature, humidity and brightness
  - CSV as database
  - Accurate SVG termometer built with Figma

## Set up<br>
  Connect the Arduino Uno, set up the firmata library on the arduino and install the python dependency. (optional)<br> 
  <br>
  `pip install flask requests`<br>
  `git clone https://github.com/BRISINGR-01/Fontys-projects.git`<br>
  `cd /Greenhouse`<br>
  `python app.py`<br>
  `flask run`
