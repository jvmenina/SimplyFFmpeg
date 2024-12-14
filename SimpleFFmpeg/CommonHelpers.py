import os


def print_log(message: str) -> None:
    print(f">> (LOG) {message}")
    return

def is_output_path_valid(output_path: str) -> bool:
    output_directory: str
    output_file: str
    output_directory, output_file = os.path.split(output_path)
    
    output_file_name: str
    output_file_extension: str
    output_file_name, output_file_extension = os.path.splitext(output_file)
    
    return os.path.isdir(output_directory) and len(output_file_name) > 0 and len(output_file_extension) > 0