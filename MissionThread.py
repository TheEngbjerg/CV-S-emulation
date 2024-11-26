import json
import logging.config
import uuid
from orbitalPositionThread_test import orbitalPositionThread_test # Import the other class
import time
import numpy as np
import os
from Task_test import Task
import cv2
import logging 
import threading

# Configure logging 
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("task_logger.log"),     # Save logs into a file
        logging.StreamHandler()     # Also log to the console
    ]
)

class MissionThread(threading.Thread):

    def __init__(self, configPath:json, group = None, target = None, name = None, args = ..., kwargs = None, *, daemon = None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        """
        Initialize the MissionThread with configuration data.
        """
         
        # Instance Attributes
        self.configPath = configPath
        self.IMAGEPATH = r"C:\Users\Phuon\OneDrive\Dokumenter\GitHub\CV-S-emulation\test"
        self.missions = []
        self.myMissions = []
        self.files = [] 
        self.satelliteID = uuid.getnode()
    

        logging.info("Initializing MissionThread for satelliteID: %s", self.satelliteID)

        #Check if image directory exist 
        if not os.path.exists(self.IMAGEPATH):
             logging.critical("Image directory does not exist: %s", self.IMAGEPATH)
             raise FileNotFoundError(f"Directory not found {self.IMAGEPATH}")
        self.files = os.listdir(self.IMAGEPATH)
        logging.debug("Image files found: %s", self.files)


        # Load and parse JSON configuration 
        try:
            with open(self.configPath, 'r') as file: 
                configData = json.load(file) # Parsed JSON data as a Python dictionary or list
            self.missions = configData.get("missions")  # Extract only the missions data 
            logging.info("Configuration loaded successfully from %s", self.configPath)
            logging.debug("Parsed missions: %s", self.missions)
        except Exception as e:
             logging.error("Failed to load configuration: %s", e)
             raise
         
        # Filter relevant missions 
        orbital_thread = orbitalPositionThread_test()
        for mission in self.missions:
             logging.debug("Checking mission: %s", mission)
             if mission.get("satellite_id") == self.satelliteID and orbital_thread.canExecuteMission(mission.get("location_radian"), mission.get("orbit_number")):
                 self.myMissions.append(mission)
                 logging.info("Mission added: %s", mission)
             else: 
                 logging.warning("No valid missions found for missions: %s", mission)


    # Method

    def __createTask(self, MACaddr ,timeLimit, file, location):
        """
        Create a task 
        """
        taskMAC = MACaddr
        logging.debug("Creating task with taskMAC: %s, file: %s, location: %s", taskMAC, file, location)
        task = Task(timeLimit)

        image = cv2.imread(file)

        if image is None:
            logging.warning("Failed to load image: %s", file)
            return

        task.appendImage(file,image,location)
        logging.info("Task created for file: %s", file)




    def run(self):
        """
        Main loop for executing mission
        """
        try: 
            logging.info("Starting mission thread")
            while True:
                for mission in self.myMissions:
                    logging.debug("Processing mission: %s", mission)
                    satellite_id = mission.get("satellite_id")
                    location_radian = mission.get("location_radian")
                    orbit_number = mission.get("orbit_number")
                    pictures_number = mission.get("pictures_number", 0)
                    time_limit = mission.get("time_limit", 0)

                    if None in (satellite_id, location_radian, orbit_number, pictures_number, time_limit):
                        logging.error("Invalid mission data: %s", mission)
                        continue

                    imageList = np.random.choice(self.files, pictures_number, replace = True) #replace change to false, when there is enough images
                    logging.debug("Selected images: %s", imageList)
                    for image in imageList:
                        # Load the image
                        file = os.path.join(self.IMAGEPATH, image)
                        self.__createTask(self.satelliteID, time_limit, file, location_radian)
                    
                    logging.info("Mission completed: %s", mission)
                    time.sleep(2) #sleep for 2 sec

        except KeyboardInterrupt:  #bare for at stoppe 
            print("Execution interrupted by user.")  


fileName = r"C:\Users\Phuon\OneDrive\Dokumenter\GitHub\CV-S-emulation\config_test.JSON"

m1 = MissionThread(fileName)
m1.run()