

from roboflow import Roboflow
rf = Roboflow(api_key="HS58u7xh7hXr8f5aIFiJ")
project = rf.workspace("vaibhav-sez14").project("peolpe-counting-nrcdv")
version = project.version(1)
dataset = version.download("yolov8")
                