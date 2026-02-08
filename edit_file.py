def swap_name(new_name):
    with open("data.txt", "r") as file:
        lines = file.readlines()

    lines[0] = new_name + "\n"

    with open("data.txt", "w") as file:
        file.writelines(lines)



def swap_character_id(character_id):
    with open("data.txt", "r") as file:
        lines = file.readlines()

    lines[1] = str(character_id) + "\n"

    with open("data.txt", "w") as file:
        file.writelines(lines)



def get_name():
    with open("data.txt", "r") as file:
        lines = file.readlines()
    return lines[0][:-1]



def get_character_id():
    with open("data.txt", "r") as file:
        lines = file.readlines()
    
    return int(lines[1])



def get_positions():
    with open("maps/map1data.txt", "r") as file:
        line = file.readline()
    
    return line