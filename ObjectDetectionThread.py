from ultralytics import YOLO
from ultralytics.engine.results import Results
import ultralytics
from pathlib import Path, PurePath
import threading
import subprocess
import torch
import logging
from getmac import get_mac_address

from MessageClasses import ProcessedDataMessage
from CommunicationThread import CommunicationThread
from TaskHandlerThread import TaskHandlerThread
from Task import Task

# Configure logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()     # Also log to the console
    ]
)

class ObjectDetectionThread(threading.Thread):
    """ Class used for running inference on images, using a YOLOv8 model.
    """

    def __init__(self, PATH_TO_MODEL, communicationThread: CommunicationThread, taskHandlerThread: TaskHandlerThread):
        super().__init__()
        self.PATH_TO_MODEL = PATH_TO_MODEL #for loading the model.
        self.AVAILABLE_FREQUENCIES = [306000000, 408000000, 510000000, 612000000,642750000]
        self.model = self.loadModel() # loading model automatically.
        self.communicationThread = communicationThread
        self.taskHandlerThread = taskHandlerThread
        self._stop_event = threading.Event()
        self.no_tasks = threading.Event() #for waiting.
        dummy_input = torch.rand(1, 3, 640, 640).to('cuda') #for model loading
        self.model.predict(dummy_input) #used to load model faster.
        self.satelliteID = int(get_mac_address().replace(":",""),16)
        self.total_cropped_images = 0

    
    def loadModel(self):
        """Method which is automatically called when ObjectDetectionThread 
        object instance is initialised. This way, the correct model is loaded when initialising the object instance.

        Returns:
            YOLO: a YOLO object instance, using the model specified by PATH_TO_MODEL.
        """
        model = YOLO(self.PATH_TO_MODEL, "detect")
        return model
    
    def runInference(self, TaskFrequencyList: tuple[Task, float]) -> Results:
        """Method used for running inference on a specific imageDataMessage object instance - which the satellite would have received or captured itself.

        Args:
            TaskFrequencyList tuple[Task, float]: The task to be executed and its frequency

        Returns:
            tuple[Results, str]: a object instance, ready to be sent to the ground station, with the results of the inference.
        """
        # Getting image file from task.
        imageObject = TaskFrequencyList[0]
        image = imageObject.getImage()

        # Set frequency of GPU:
        frequency = TaskFrequencyList[1]
        self.changeFrequency(frequency=frequency)

        logging.info("Running Object Detection on task %s with image file %s", imageObject.getTaskID(), imageObject.getFileName())
        # Running inference on image, using the GPU
        results = self.model.predict(image, device=0)

        logging.info("Finished Object Detection for task %s with image file %s", imageObject.getTaskID(), imageObject.getFileName())

        return results[0]

    def getMessageList(self, result: Results, task: Task):
        bounding_box_list = result.boxes.xyxy.tolist() # Save bounding boxes as list.
        # Necessary for renaming cropped images.
        image_file_name = PurePath(task.getFileName()).name
        crop_number = 0 

        finished_message_list = [] # List for storing ProcessedDataMessage
        
        if self.communicationThread.orbitalPositionThread.getSatClosestToGround() == self.satelliteID:
                firstHopID = None
        else:
            priority_list = self.communicationThread.orbitalPositionThread.getSatellitePriorityList()
            firstHopID = None
            break_out = False
            for i in range(len(priority_list)):
                for j in self.communicationThread.connections:
                    if priority_list[-(i+1)] == j:
                        firstHopID = j
                        break_out = True
                        break
                if break_out:
                    break
        
        for box in bounding_box_list:
            # Creating one ProcessedDataMessage per boat found.
            x_min, y_min, x_max, y_max = map(int, box)
            finished_message = ProcessedDataMessage(result.orig_img[y_min:y_max, x_min:x_max], 
                                                    task.getLocation(), 
                                                    task.getUnixTimestamp(), 
                                                    f"crop{crop_number}_" + image_file_name, 
                                                    box,
                                                    firstHopID=firstHopID)

            finished_message_list.append(finished_message)
            crop_number += 1
        
        self.total_cropped_images += crop_number
        return finished_message_list
    
    def changeFrequency(self, frequency: float) -> None:
        """This function fixes the gpu at the closest frequency available to the input frequency
        Args:
            frequency (float): The desired frequency
        """
        frequencies = [f for f in self.AVAILABLE_FREQUENCIES if f >= frequency]
        min_frequency = min(frequencies)
        command = (
            'echo 1234 | sudo -S sh -c "cd /sys/devices/platform/17000000.gpu/devfreq/17000000.gpu && '
            f'echo {min_frequency} | tee min_freq max_freq"'
        )

        subprocess.run(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        logging.info("GPU frequency set to %s Hz", min_frequency)

    def sendProcessedDataMessage(self, message_list: list[ProcessedDataMessage]):
        """Simple method for moving the PrcessedDataMessage object instance to the transmission queue in the CommunicationThread object instance.

        Args:
            message (ProcessedDataMessage): the ProcessedDataMessage object instance returned by the runInference method.
            communication_thread (CommunicationThread): the CommunicationThread object instance used by the communication thread.

        Returns:
            None: none
        """
        for message in message_list:
            self.communicationThread.addTransmission(message)
        return None

    def run(self):
        while not self._stop_event.is_set():
            if not self.taskHandlerThread.allocatedTasks.isEmpty():
                print("Running Object detection")
                nextTask = self.taskHandlerThread.allocatedTasks.nextTask()
                result = self.runInference(nextTask)
                processedDataList = self.getMessageList(result, nextTask[0])
                self.sendProcessedDataMessage(processedDataList)
                logging.info("Total boats found: %s", self.total_cropped_images)
            else:
                #Set the gpu frequency to smallest possible frequency to save on power
                self.changeFrequency(self.AVAILABLE_FREQUENCIES[0])
                self.no_tasks.wait(1)


    def stop(self):
        self._stop_event.set()

if __name__ == "__main__":
    import cv2
    import os
    HOME = Path.cwd()
    current_dir = Path(__file__).parent.resolve()
    cv_model_path = current_dir / "models" / "yolov8m_best.engine"
    objectDetectionThread = ObjectDetectionThread(cv_model_path,None, None)
    # Prepare statistics
    preprocessing_times = []
    inference_times = []
    postprocessing_times = []
    {HOME}
    test_imgs_path = list(Path('images').glob('*.jpg'))
    tasks = [Task(1,1,1) for _ in test_imgs_path]
    for task, img in zip(tasks, test_imgs_path):
        task.appendImage(img.name, cv2.imread(img), 1+0j) 
    
    for task in tasks:
        result, _ = objectDetectionThread.runInference((task, 612000000.0))
        preprocessing_times.append(result.speed["preprocess"])
        inference_times.append(result.speed["inference"])
        postprocessing_times.append(result.speed["postprocess"])
    
    avg_preprocessing_time = sum(preprocessing_times) / len(preprocessing_times)
    avg_inference_time = sum(inference_times) / len(inference_times)
    avg_postprocessing_time = sum(postprocessing_times) / len(postprocessing_times)

    print("\n=== Average Timing Results ===")
    print(f"Average Preprocessing Time: {avg_preprocessing_time:.4f} miliseconds")
    print(f"Average Inference Time: {avg_inference_time:.4f} miliseconds")
    print(f"Average Post-processing Time: {avg_postprocessing_time:.4f} miliseconds")