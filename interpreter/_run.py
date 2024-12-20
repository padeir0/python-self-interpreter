#!/bin/python
from parser import parse
import os
import sys

def do_the_thing(dict, modname):
    root, err = parse(dict[modname], True)
    if err != None:
        print(err)
    else:
        print(root)

def get_python_files(directory_path):
    files_contents = {}
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        modname = file[:len(file)-3] # remove ".py" do final da string
                        files_contents[modname] = f.read()
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")
    
    return files_contents

def get_root_dir(file_path):
    abs_path = os.path.abspath(file_path)
    components = abs_path.split(os.sep)
    if components:
        path = os.sep.join(components[:len(components)-1])
        return path
    else:
        return None

def run_single_file(file_path):
    if not file_path.endswith(".py"):
        print("not a python file")
        return
    root = get_root_dir(file_path)
    if root == None:
        print("invalid file path")
        return
    modname = os.path.basename(file_path)
    modname = modname[:len(modname)-3] # remove ".py"
    files = get_python_files(root)
    do_the_thing(files, modname)

def test_whole_dir(folder_path):
    files = get_python_files(folder_path)
    print(files)
    
if __name__ == "__main__":
    if len(sys.argv) == 2:
        file_path = sys.argv[1]
        run_single_file(file_path)
    elif len(sys.argv) == 3:
        keyword = sys.argv[1]
        if keyword == "test":
            folder = sys.argv[2]
            test_whole_dir(folder)
        else:
            print("invalid parameters")
    else:
        print("no arguments provided")

