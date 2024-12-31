#!/bin/python
from parser import parse
from evaluator import evaluate
import os
import sys

def extract_offense(range, program):
    p_line_start = None
    p_index_start = 0
    p_line_end = None
    p_index_end = 0
    
    lines = 0
    columns = 0
    index = 0

    for c in program:
        index += 1
        columns += 1
        if c == "\n":
            lines += 1
            columns = 0

        if lines == range.start.line and p_line_start == None:
            p_line_start = index
        if lines == range.end.line:
            p_line_end = index

        if lines == range.start.line and columns == range.start.column:
            p_index_start = index
        if lines == range.end.line and columns == range.end.column:
            p_index_end = index

    offense = program[p_line_start:p_index_start]
    offense += "\033[0;31m"
    offense += program[p_index_start:p_index_end]
    offense += "\033[0m"
    offense += program[p_index_end:p_line_end]

    return offense

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
    err = evaluate(files, modname)
    if err != None:
        e = err.copy()
        e.correct_editor_view() 
        print(e)
        code = files[modname]
        if err.range != None:
            print("\t" + extract_offense(err.range, code))

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

