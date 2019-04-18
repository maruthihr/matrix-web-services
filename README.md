# matrix-web-services
Implementation of the comp 598 cloud project
We named our project as Matrix Web Services (MWS). 

# Getting Started
The MWS can be started by running the __main__.py file on the project root directory. When started, the MWS gives a command line interface where users can enter different commands supported by the MWS. The MWS Command Line Interface (CLI) looks like below:

![MWS CLI](/images/mws_cli.png)

# Commands:
# 1. start 
  start <application name> <number of workers to begin with>
  start an application on the MWS cloud. Specify the application name and initial number of workers allocated for this application
# 2. stop 
  stop <applicatin name>
  Stop an appliciation
# 3. list 
  ls <appliation name>
  List the number of workers for an application
# 4. scale 
  scale <application name> <count>
  Add or Remove a worker manually. positive count adds specified number of workers. Negative cound removes specified number of workers
# 4. autoscale 
  autoscale <application name>
  Start auto-scaling feature for an application. The auto-scaling is done based on the total CPU usage of the application
# 5. exit
# 6. help
  

