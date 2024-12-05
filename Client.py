import socket
import time
import cv2
from pickle import dumps
from Task import Task
from MessageClasses import ImageDataMessage, ProcessedDataMessage
from numpy import asarray, ones
import sys
from PIL import Image
import numpy as np


SERVER_IP = "192.168.0.106"
SERVER_PORT = 4500


# Load image
image_path = '/Users/tobiaslundgaard/Desktop/Semester 5/Projekt5/donkey.jpg'
#image = cv2.imread(image_path)
image = Image.open(image_path)
print(image)
width, height = image.size
new_size = (width//6, height//6)
resized_image = image.resize(new_size)
#numpydata = asarray(resized_image)


# Create Task and append compressed image
task = Task(satelliteID=1, taskCount=1, timeLimit=300)
task.appendImage(fileName=image_path, image=resized_image, location=complex(10.0, 20.0))
# Create the ProcessedDataMessage

message = ProcessedDataMessage(
    image = resized_image,
    location = complex(10.0, 20.0),
    unixTimeStamp = 500,
    fileName = image_path,
    boundingBox = ((50, 50), (200, 200)),
    firstHopID = 42
)
# Create and serialize ImageDataMessage
first_hop_id = 100
image_message = ImageDataMessage(payload=task, firstHopID=first_hop_id)
serialized_message = dumps(image_message)
serialized_message2 = dumps(message)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        udp_limit = 65507  # Maximum safe UDP payload size
        message_size = sys.getsizeof(serialized_message)
        print(sys.getsizeof(serialized_message2))
        print(f"Serialized message size: {len(serialized_message)} bytes")
        if message_size > udp_limit:
            print(f"Warning: The message size exceeds the UDP limit of {udp_limit} bytes!")
        else:
            print("Message size is within the safe UDP limit.")
        print(client_socket.sendto(serialized_message, (SERVER_IP, SERVER_PORT)))
        client_socket.sendto(serialized_message, (SERVER_IP, SERVER_PORT))
        client_socket.sendto(serialized_message2, (SERVER_IP, SERVER_PORT))
        print("Message sent successfully.")
except Exception as e:
    print(f"Error sending message: {e}")