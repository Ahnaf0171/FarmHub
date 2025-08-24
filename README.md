Assignment: FarmHub
Name: Abdullah Ahnaf
Email: abdullahahnaf4567@gmail.com
Contact: 01660120610

I completed the full project with your requirements.here is 2 folder core and reporting folder. I used swagger,
simple jwt authentication system, Custom admin panel

Core Service (Django + DRF):
So first try to check these requirements: Core Service (Django + DRF). so open the project and create a virtual
environment first then run this command
pip install -r requirement.txt
so that all dependencies are installed for my project.
In the terminal write
py manage.py runserver

Admin
username: admin
Password: 12345
Agent
Username:tanvir
Password: Ahnaf@0171
Username: orpa
Password: Ahnaf@0171
Farmer
Username:ahad
Password: Ahnaf@0171
Username: shimul
Password: Ahnaf@0171
Then go to this url
http://127.0.0.1:8000/swagger/
Now you can see the full project url.
If you go to this url then you can login in Custom admin panel for non technical users
http://127.0.0.1:8000/admin/
So now if i want describe how it works if you go to this url then you can register yourself as a farmer or an agent(method: post)
http://127.0.0.1:8000/api/auth/register/
Then if you want to see the all users then first you have to give your token so for collecting your token just go to this url.
If you use this url then login and get a token and and copy the access token from this two tokens
http://127.0.0.1:8000/api/token/
[note: the token is expired after a limited time]
If you login as an admin or agent or farmer but when you want to see all the users you have to pass the admin token. 
If I pass the agent token then you will get only your agent
information and also get the farmers info who are under this agent. If you pass the farmer token you only get farmer information.
So now if you pass your token using Postman through the authorization and send the token then go to this url (you can check 
with a different token). Also I can see my users in another approach, click the login button and then send the username and
password then I can see the users.
http://127.0.0.1:8000/api/users/ 
If i register an agent i have to pass the admin token if i pass the agent or farmer token i cannot register an agent here is the url
http://127.0.0.1:8000/api/users/agents/ 
If i register a farmer i have to pass the admin or agent token if i pass the farmer token i cannot register an agent here is the url another issue is without any farm i cannot create a farmer so for creating a farmer first i have to create a farm
http://127.0.0.1:8000/api/users/farmers/ 
No i f i want to create a farm must i have an agent without an agent. I cannot create a farm so if i send my admin token 
then i have to send the agent id. If i send an agent token i don’t have to send the agent id like that. Here i pass the 
admin token so i write this code (method post) 
http://127.0.0.1:8000/api/farms/ 
{ "name": "tanvir cattle farm", "location": "rampura", "agent": 17 } 
If i pass the agent token i have to send only this code 
{ "name": "tanvir 2 cattle farm", "location": "rampura ulan" } 
If i want to see all farms i have to login the admin token if i login the agent token then it will show only the agent farmers
information if i login the farmers token it will show the only his farms information (method :get)
http://127.0.0.1:8000/api/farms/ 
If i want to see a farm detail then i can see, edit or delete it if my token is an admin token if my token is an agent 
token if the farms under this agent he or she can delete or edit the information (method PUT, DELETE, GET)
http://127.0.0.1:8000/api/farms/3/ 
If you register a cow then if the token is a farmer token then you go to this url and write this code if you send 
an admin token then you have to send a farm id number and agent id so i send the farmer token (method POST)
http://127.0.0.1:8000/api/cows/ 
{ "tag_number": "b1", "breed": "shahiyal", "birth_date": "2024-11-07" }
You can see the number of cows using admin token (method: get)
http://127.0.0.1:8000/api/cows/ 
You can see, edit, delete a specific cow details using this url but send the admin token if you send the agent token if he is not registered for this cow it will show permission denied
http://127.0.0.1:8000/api/cows/1/ 
I just explain how it works. Another many features i include. you can go to this url and also check is it working or not.
I checked all the urls which perfectly works. Just i am sharing this urls and i shared before how to check this process.
so i do not explain the process but must you have a token. So i explain how to get a token
http://127.0.0.1:8000/api/milk/                 (method get, post)
http://127.0.0.1:8000/api/milk/1/               (method get, put, delete)
http://127.0.0.1:8000/api/activities/           (method get, post)
http://127.0.0.1:8000/api/activities/1/          (method get, put, delete)
[Note: i check this urls using Postman software] [limitation: i can use throttling for security purpose but in short time i cannot implementthis feature] 

Reporting Service (FastAPI):
In this part all my files are in my reporting folder. I used my existing database for my reporting service(fastAPI) database.
So I don't have to create any other database. I handled it
using my database.py file. To use this reporting service (fastAPI) I have to run 2 servers at a time. My Core Service (Django + DRF) server + my Reporting Service (FastAPI) server. So in VScode terminal i sent this command 
py manage.py runserver 8000 
And in my actual command prompt i go to the folder directory and activate the virtual environment then write this command 
uvicorn reporting.main:app --reload --port 8001 
So 2 servers are working at a time with 2 different ports. So first i collect the jwt token from the this url
http://127.0.0.1:8000/api/token/
Then i after getting this token in my postman software i send this token then in the urls and get the result using postman software
http://127.0.0.1:8001/reports/milk-production          (method: get)
http://127.0.0.1:8001/reports/farm-summary             (method: get)
http://127.0.0.1:8001/reports/recent-activities        (method: get) 
[limitations: i can use pedantic package for authorization  and also i can generate the report as a text format and more organized way 
but for short time i cannot do this properly]