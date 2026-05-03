# Liam Pearson
# Multiplayer Racing Game File Editing Functions

def swap_name(new_name):
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    lines[0] = new_name + "\n"

    with open("data/data.txt", "w") as file:
        file.writelines(lines)



def swap_character_id(character_id):
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    lines[1] = str(character_id) + "\n"

    with open("data/data.txt", "w") as file:
        file.writelines(lines)



def get_name():
    with open("data/data.txt", "r") as file:
        lines = file.readlines()
    return lines[0][:-1]



def get_character_id():
    with open("data/data.txt", "r") as file:
        lines = file.readlines()
    
    return int(lines[1])



def get_positions(i):
    with open("data/maps/map" + str(i) + "data.txt", "r") as file:
        line = file.readline()
    
    return line



def get_vsync():
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    return True if int(lines[2]) == 1 else False



def get_fps():
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    return True if int(lines[3]) == 1 else False



def set_vsync(i):
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    lines[2] = str(i) + "\n"

    with open("data/data.txt", "w") as file:
        file.writelines(lines)



def set_fps(i):
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    lines[3] = str(i) + "\n"

    with open("data/data.txt", "w") as file:
        file.writelines(lines)



def get_controls():
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

        a = lines[4].split()
        b = [int(i) for i in a]

    return b



def set_controls(lis):
    with open("data/data.txt", "r") as file:
        lines = file.readlines()

    lines[4] = " ".join(str(i) for i in lis) + "\n"

    with open("data/data.txt", "w") as file:
        file.writelines(lines)