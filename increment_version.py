import os

VERSION_FILE = "version.txt"

def increment_version():
    if not os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "w") as f:
            f.write("1.0.0")
        return "1.0.0"
        
    with open(VERSION_FILE, "r") as f:
        version = f.read().strip()
        
    parts = version.split('.')
    if len(parts) != 3:
        parts = ['1', '0', '0']
        
    # Increment patch
    parts[2] = str(int(parts[2]) + 1)
    
    new_version = ".".join(parts)
    
    with open(VERSION_FILE, "w") as f:
        f.write(new_version)
        
    return new_version

if __name__ == "__main__":
    new_ver = increment_version()
    print(f"Version updated to: {new_ver}")
    # Print to stdout so batch can capture it if needed, 
    # but reading file from batch is safer usually.
