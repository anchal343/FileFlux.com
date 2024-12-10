import os
from PIL import Image

mywidth = 2000

source_dir = r"D:\bird.jpg"  # Source image path
dest_dir = r"D:\kedarnath1"  # Destination directory

def resize_pic(old_pic, new_pic, mywidth):
    img = Image.open(old_pic)
    wpercent = (mywidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((mywidth, hsize), Image.LANCZOS)
    img.save(new_pic)

def entire_directory(source_dir, dest_dir, mywidth):
    # Ensure the destination directory exists
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Check if the source path is a file or directory
    if os.path.isfile(source_dir):
        # If it's a single file, process it
        old_pic = source_dir
        new_pic = os.path.join(dest_dir, os.path.basename(source_dir))
        resize_pic(old_pic, new_pic, mywidth)
        print("Image resized and saved to:", new_pic)
    elif os.path.isdir(source_dir):
        # If it's a directory, process all image files
        files = os.listdir(source_dir)
        i = 0
        for file in files:
            old_pic = os.path.join(source_dir, file)
            if os.path.isfile(old_pic):
                new_pic = os.path.join(dest_dir, file)
                resize_pic(old_pic, new_pic, mywidth)
                i += 1
                print(i, "done:", file)
    else:
        print("Source path is not valid.")

# Call the function
entire_directory(source_dir, dest_dir, mywidth)