# PCB15-04 Pizza

# Resources
pizza svgs - https://www.svgrepo.com/vectors/pizza/<br>
authentication tutorial - https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login<br>
logo - https://looka.com/<br>
ico convertor - https://convertico.com/<br>
grid - https://www.w3docs.com/snippets/css/how-to-center-the-content-in-grid.html<br>
     - https://www.digitalocean.com/community/tutorials/css-align-justify<br>
drawing pizza - https://www.w3schools.com/graphics/svg_circle.asp<br>
csv inijection - https://owasp.org/www-community/attacks/CSV_Injection<br>
               - https://patchstack.com/articles/patchstack-weekly-what-is-csv-injection/#:~:text=CSV%20injection%20occurs%20when%20websites,is%20still%20considered%20high%20risk.<br>
cryptography - https://cryptography.io/en/latest/faq/#:~:text=the%20PyCA%20team.-,Why%20use%20cryptography%3F,%C2%B6,-If%20you%E2%80%99ve%20done<br>
# Run the application

```
git clone https://git.fhict.nl/I510937/pcb15-04-pizza.git
cd ./pcb15-04-pizza
pip install flask flask_login cryptography flask_socketio
```

create a dev.py file with the following variables<br>
```
SECRET_KEY=""
ENCRYPTION_KEY=b'' # generated by calling Fernet.generate_key() (from cryptography.fernet import Fernet)
EMAIL_SENDER=""
EMAIL_PASSWORD=""
```

run the apps (each command in a seperate terminal)
```
python app.py
python "oven server.py"

```
