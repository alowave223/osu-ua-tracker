# osu-ua-tracker
Simple python 3.9 script to track scores and top moving in discord!

# How to use?
1. Create osu! Api client and save your client's ID and Secret (you'll need it for configuration file)
Steps to create osu! api client:
Go to https://osu.ppy.sh/home/account/edit and scroll to very bottom
Click on "New OAuth Application" and fill "Application Name" fild with anything you want
Fill the "Application Callback URL" with http://localhost/ then click "Register application"
Done! (Don't forget to save the ID and secret of your application!)
2. Rename .env.example to .env and fill the variables with info you just get (read comments in .env)
3. Go to root directory of project and type python3.9 main.py
