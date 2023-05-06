import os
import sys

def load_classes(classes_file:str):
    with open(classes_file) as file:
        available_classes = file.read().split('\n')[:-1]
        return available_classes
    


    