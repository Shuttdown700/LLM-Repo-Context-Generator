import os
import argparse
from pathlib import Path

def generate_code_dump(root_dir, extensions, output_file, exclude_dirs):
    root_path = Path(root_dir).resolve()
    output_path = Path(output_file).resolve()
    
    # Get the absolute path of this script to avoid self-ingestion
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        # Fallback if running in an interactive environment where __file__ isn't defined
        script_path = None
    
    # Baseline junk directories that should always be ignored
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.venv', 
                   'env', '.idea', '.vscode', 'flashenv', 'dist', 'build', 'target'}
    
    # Add any user-specified directories to the ignore set
    if exclude_dirs:
        ignore_dirs.update(exclude_dirs)
    
    # Ensure extensions start with a dot
    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
    
    count = 0
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Modify dirnames in-place to skip ignored directories
            dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
            
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    file_path = Path(dirpath) / filename
                    resolved_file_path = file_path.resolve()
                    
                    # Prevent the script from reading itself or its own output file
                    if resolved_file_path == output_path or resolved_file_path == script_path:
                        continue
                        
                    relative_path = file_path.relative_to(root_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='replace') as infile:
                            content = infile.read()
                            
                        outfile.write("=" * 80 + "\n")
                        outfile.write(f"File: {filename}\n")
                        outfile.write(f"Path: {relative_path}\n")
                        outfile.write("=" * 80 + "\n")
                        outfile.write(content + "\n\n")
                        
                        count += 1
                        
                    except Exception as e:
                        print(f"Skipping {relative_path} due to read error: {e}")

    print(f"Success! Appended {count} files to '{output_file}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aggregate specified code files into a single text file.")
    
    parser.add_argument("-d", 
                        "--directory", 
                        type=str, 
                        default=".", 
                        help="Root directory to scan (default: current directory)")
    
    parser.add_argument("-e", 
                        "--extensions", 
                        type=str, 
                        nargs="+", 
                        default=["py", "md", "txt", "json","csv","sh","yml","yaml"], 
                        help="File extensions to include (default: py md txt json)")
    
    # NEW: Custom directory exclusions
    parser.add_argument("-x", 
                        "--exclude-dirs", 
                        type=str, 
                        nargs="+", 
                        default=["__MACOSX"], 
                        help="Additional directories to exclude (default: __MACOSX)")
    
    parser.add_argument("-o", 
                        "--output", 
                        type=str, 
                        default="file_content_tree.txt", 
                        help="Output file name (default: file_tree.txt)")
    
    args = parser.parse_args()
    generate_code_dump(args.directory, args.extensions, args.output, args.exclude_dirs)