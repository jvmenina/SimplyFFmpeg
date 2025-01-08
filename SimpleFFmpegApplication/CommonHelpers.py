import os
from typing import Any
from sys import stderr


def print_log(*message: Any) -> None:
    print(">> (LOG) ", end="")
    print(*message, sep=" ")
    return

def print_error(*message: Any) -> None:
    print(">> (LOG) ", end="", file=stderr)
    print(*message, sep=" ", file=stderr)
    return

def is_output_path_valid(output_path: str) -> bool:
    output_directory: str
    output_file: str
    output_directory, output_file = os.path.split(output_path)
    
    output_file_name: str
    output_file_extension: str
    output_file_name, output_file_extension = os.path.splitext(output_file)
    
    return os.path.isdir(output_directory) and len(output_file_name) > 0 and len(output_file_extension) > 0