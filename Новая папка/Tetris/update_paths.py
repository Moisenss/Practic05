import re

def update_file_paths():
    # Read the original file
    with open('tetris.py', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Update image paths to include 'images/'
    content = re.sub(
        r'Image\.open\("((?!images/)(?!sounds/))([^"]+\.(?:png|jpg|jpeg))"\)',
        r'Image.open("images/\2")',
        content
    )
    
    # Update audio paths to include 'sounds/'
    content = re.sub(
        r'play_sound\("([^"]+\.wav)"\)',
        r'play_sound("sounds/\1")',
        content
    )
    
    content = re.sub(
        r'pyglet\.media\.load\("([^"]+\.wav)"\)',
        r'pyglet.media.load("sounds/\1")',
        content
    )
    
    # Write the updated content back to the file
    with open('tetris.py', 'w', encoding='utf-8') as file:
        file.write(content)
    
    print("File paths have been updated successfully!")

if __name__ == "__main__":
    update_file_paths()
