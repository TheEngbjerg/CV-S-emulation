#Libraries
import random
import threading
from Task import Task
from MessageClasses import *
#from MissionThread import *
from CommunicationThread import CommunicationThread


class TaskHandlerThread(threading.Thread):

    def __init__(self, communicationThread: CommunicationThread):
        super().__init__()
        self.running = True
        self.__allocatedTasks = []
        self.__unallocatedTasks = []
        self.communicationThread = communicationThread


    def run(self):
        """
        Method to initiate the different threads in the system(Main loop maybe?)
        """
        while self.running:
            pass

    # Det her skal lige fikses, så det kører fra run().
    # mucho fix
    def allocateTaskToSelf(self, task: Task, __unallocatedTasks: list, __allocatedTasks: list):
        """
        Method used to either allocate a task to a satellite itself, or send a request message to another satellite
        """
        if __unallocatedTasks != None:
            task = __unallocatedTasks[0]
            x = "Insert Kristian Meth"
            if x == True:
                self.__allocatedTasks.append[task]
            else:
                TaskHandlerThread.sendRequest(Task)
        else:
            pass
        

    def sendRequest(self, task: Task):
        """
        Sends a request message for a task to the CommunicationThread.
        """
        
        # Create a RequestMessage object
        sendRequestMessage = RequestMessage(
            unixTimeLimit=task.getUnixTimestampLimit(),
            taskID=task.getTaskID()
        )

        # Print the message object directly
        print(f"Sending message: {sendRequestMessage}")

        # Add the message to the CommunicationThread
        self.communicationThread.addTransmission(sendRequestMessage)

        # Return the task ID and time limit
        return sendRequestMessage.getTaskID(), sendRequestMessage.getUnixTimeLimit()


    def sendRespond(self, task: Task, message: Message):
        """
        Method to send a respond to other satellites telling them they can perform the requested task
        """
        sendRespondMessage = RespondMessage(
            taskID=task.getTaskID(),
            source=task.getSource(),
            firstHopID = message.lastSenderID
        )
        # Vi skal lige fikse naming og method her.
        # Add the message to the CommunicationThread
        self.communicationThread.addTransmission(sendRespondMessage)
 

        # Print and return
        print(f"Sending: {sendRespondMessage}")
        return sendRespondMessage.getTaskID(), sendRespondMessage.getTaskID()



    def sendDataPacket(self, task: Task, message: Message):
        """
        Send task packet to 
        """
        sendDataMessage = ImageDataMessage(payload=task, firstHopID=message.lastSenderID)

        self.communicationThread.addTransmission(sendDataMessage)
        return sendDataMessage


    def getAcceptedTaskTotal(self, __allocatedTasks: list):
        """
        Method to get the ammount of accepted tasks a satellite has
        """
        return len(__allocatedTasks) + self.communicationThread.getTotalAcceptedTasks()


    def enqueueUnallocatedTask(self, task: Task):
        self.__unallocatedTasks.append(task)
        

    def appendTask(self, task: Task):
        self.__allocatedTasks.append(task)
    
    def appendUnallocatedTask(self, task: Task):
        self.__unallocatedTasks.append(task)


#####################################################################################################
class CommunicationThread(threading.Thread):

    def __init__(self):
        super().__init__()

        self.tasklist = []

    def addTransmission(self, message: Message):
        self.tasklist.append(message)
        print(f"The tasklist is now: {[str(msg) for msg in self.tasklist]}")

    def getTotalAcceptedTasks(self):
        return 0

#Test for the different messages
thread = TaskHandlerThread()
CommThread = CommunicationThread()

thread.start()
CommThread.start() 

"""
Generate a random task
"""
# Generate a random 48-bit integer for satelliteID
satelliteID = random.randint(0, 2**48 - 1)
# Generate a random 8-bit integer for incrementingID (or use a counter if needed)
incrementingID = random.randint(0, 255)

# Construct self.taskID
taskIDTest = satelliteID.to_bytes(6, 'big') + incrementingID.to_bytes(1, 'big')

# Create instances
task = Task(satelliteID, incrementingID, timeLimit=3600)  # Create a Task with a 1-hour limit

# Send a task request
taskID, timeLimit = thread.sendRespond(task)  # Call on the instance
print(f"TaskID: {taskID}, TimeLimit: {timeLimit}")

#send a task respond
taskID, source= thread.sendRespond(task)  # Call on the instance
#####################################################################################################