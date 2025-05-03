###
# Train an ultralytics YOLOv8 model on a custom dataset.
###

import multiprocessing
from ultralytics import YOLO
import torch

def main():
    # Point to the last weight of previous model training to refine it
    # model = YOLO("fyp/v4/weights/last.pt")
    # Or start from scratch
    model = YOLO("yolov8l.pt")

    model.train(
            # Point to data.yaml file of desired dataset
            data=fr"C:\Development\Project\datasets\v1\data.yaml", 
            batch=4, 
            # Directory to store the project
            project="fish_models", 
            # Directory name for the current training run
            name="l640",
            device=0,
            imgsz=640,
            # Set to True when refining an existing model, False when starting from scratch
            pretrained=False
            )

if __name__ == "__main__":
    multiprocessing.freeze_support()    
    torch.cuda.empty_cache()
    main()
  