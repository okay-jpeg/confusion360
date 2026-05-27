import traceback
import adsk.core
import adsk.fusion
import re

app = adsk.core.Application.get()
ui  = app.userInterface
doc = app.activeDocument

def find_folder_by_name(parent_folder, target_name):
    folders = parent_folder.dataFolders
    for i in range(folders.count):
        folder = folders.item(i)
        if folder.name == target_name:
            return folder
    return None

def find_part_folder(root_folder, part_number):
    parts = part_number.split("-")

    level1 = parts[0]
    level2 = f"{parts[0]}-{parts[1]}"
    level3 = f"{parts[0]}-{parts[1]}-{parts[2]}"

    top_folder = find_folder_by_name(root_folder, level1)

    if not top_folder:
        return None

    sub_folder = find_folder_by_name(top_folder, level2)

    if not sub_folder:
        return None

    part_folder = find_folder_by_name(sub_folder, level3)

    return part_folder

def open_latest_file(folder, part_number):

    files = folder.dataFiles

    for i in range(files.count):

        file = files.item(i)
        if file.name == part_number:
            app.documents.open(file)
            return
        else:
            ui.messageBox(f"File does not exist")
            return

def run(_context: str):

    try:
        data = app.data
        active_hub = data.activeHub
        mch_folder = active_hub.dataProjects.item(0)

        root_folder = mch_folder.rootFolder
        subfolders = root_folder.dataFolders
        
        pattern = r'[A-Z]+-[A-Z]+-P\d+-V\d-C\d-R\d'

        part_number, _ = ui.inputBox("Enter a full part number")
        result = re.match(pattern, part_number)

        if result:
            test = find_part_folder(root_folder, part_number)

            if test:
                open_latest_file(test, part_number)
            else:
                ui.messageBox(f"Didnt find anything")
        else:
            ui.messageBox(f"Incorrect part number")
        
        
    except Exception as e:
        ui.messageBox(f"{e}")
