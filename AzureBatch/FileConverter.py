import os
import re
from zipfile import ZipFile, ZIP_DEFLATED

"""
File conversion software to rename and extract the "easy name" 
"""


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), file)

def test_replace2(folder_path):

    folder_counter = 0
    file_counter = 0

    for path, subdirs, files in os.walk(folder_path, topdown=False):
        for name in subdirs:
            matches = re.match(r".*_[A-Z]_.*", name)
            if matches is not None:
                # print(matches.string)
                new_name = f"{matches.string[:16]}_{matches.string[-16:]}"
                # print(new_name)
                # print(os.path.join(path,new_name))
                os.rename(os.path.join(path, name), os.path.join(path, new_name))
                folder_counter += 1
            else:
                if "POGO" in name or "HUGA" in name:
                    # print(name)
                    new_name = f"{name[:16]}"
                    # print(new_name)
                    # print(os.path.join(path, new_name))
                    os.rename(os.path.join(path, name), os.path.join(path, new_name))
                    folder_counter += 1

    for path, subdirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".json") or file.endswith(".json2"):
                split_file = file.split(".")
                new_name = f"{file[:16]}_{split_file[0][-30:]}.{split_file[1]}"
                # print(new_name)
                # print(os.path.join(path,new_name))
                os.rename(os.path.join(path,file), os.path.join(path, new_name))
                file_counter += 1

    #DELETE Existing ZIP's
    for path, subdirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".zip"):
                os.remove(os.path.join(path, file))

    ## ZIP Folders:
    for path, subdirs, files in os.walk(folder_path):
        for name in subdirs:
            matches = re.match(r".*_[A-Z]_.*", name)
            if matches is not None:
                folder_dir = os.path.join(path,matches.string)
                print(folder_dir)
                with ZipFile(f"{matches.string}.zip", "w", ZIP_DEFLATED) as zpf:
                    zipdir(folder_dir, zpf)
                # Move it to the right spot
                relpath = os.path.relpath(path, folder_path)
                output_dir = os.path.join(folder_path, 'outputs', relpath)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                os.rename(f"{matches.string}.zip", f"{os.path.join(output_dir, matches.string)}.zip")


if __name__ == '__main__':
    practice = 'C:\\Users\\DhruvNarayanan\\proj\\sail-on\\01. Tournaments\\01. 6M Eval\\pogo_dry_run\\practice'
    actual = 'C:\\Users\\DhruvNarayanan\\proj\\sail-on\\01. Tournaments\\01. 6M Eval\\pogo_dry_run\\pogo-test-6M-renamed'
    huga = 'C:\\Users\\DhruvNarayanan\\proj\\sail-on\\01. Tournaments\\01. 6M Eval\\huga-6M-tournaments\\huga'
    test_replace2(huga)