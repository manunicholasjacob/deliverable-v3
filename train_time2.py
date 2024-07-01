# train_time.py
import subprocess
import time

def read_header(bus):
    try:
        bridge_control_output = subprocess.check_output(["setpci", "-s", bus, "0e.w"])
        return f" : {bridge_control_output.decode().strip()}"
    except subprocess.CalledProcessError:
        return f"Error reading Bridge Control for {bus}."
    
def read_link_status(bus):
    try:
        link_status_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X12.w"])
        return link_status_output.decode().strip()
    except subprocess.CalledProcessError:
        return None
    
def read_link_capabilities(bus):
    try:
        link_capabilities_output = subprocess.check_output(["setpci", "-s", bus, "CAP_EXP+0X0c.l"])
        return link_capabilities_output.decode().strip()
    except subprocess.CalledProcessError:
        print("error")
        return None
    
def hex_to_binary(hex_string):
    binary_string = format(int(hex_string, 16), '032b')
    return binary_string

def extract_link_capabilities(hex_string):
    binary_string = hex_to_binary(hex_string)
    max_link_width = int(binary_string[-3:], 2)
    max_link_speed = int(binary_string[-9:-4], 2)
    return max_link_width, max_link_speed

def extract_link_status(hex_string):
    binary_string = hex_to_binary(hex_string)
    current_link_width = int(binary_string[-4:], 2)
    current_link_speed = int(binary_string[-10:-4], 2)
    return current_link_width, current_link_speed

def read_secondary_bus_number(bus):
    try:
        secondary_bus_output = subprocess.check_output(["setpci", "-s", bus, "19.b"])
        return secondary_bus_output.decode().strip()
    except subprocess.CalledProcessError:
        return None

def set_bridge_control(bus, value, password):
    try:
        subprocess.run(["sudo", "-S", "setpci", "-s", bus, "3e.w=" + value], input=password.encode(), check=True)
        print(f"Set Bridge Control for {bus} to {value}")
    except subprocess.CalledProcessError:
        print(f"Error setting Bridge Control for {bus}.")

def get_train_time(bdf):
    header_type = read_header(bdf)[-2:]

    # make sure that the bdf we are given has a downstream port to train with
    if header_type != "01":
        print("Invalid BDF")
        return -1
    
    # I want to read what the speed and width capabilities of the bdf given and the one that is connected to it underneath
    primary_link_speed_capabilities = read_link_capabilities(bdf)[-1]
    secondary_bus = read_secondary_bus_number(bdf) + ":00.0"
    secondary_link_speed_capabilities = read_link_capabilities(secondary_bus)[-1]
    train_speed = min(primary_link_speed_capabilities, secondary_link_speed_capabilities)

    primary_link_width_capabilities = hex_to_binary(read_link_capabilities(bdf))[-9:-4]
    secondary_link_width_capabilities = hex_to_binary(read_link_capabilities(secondary_bus))[-9:-4]
    train_width = min(primary_link_width_capabilities, secondary_link_width_capabilities)

    # SBR and measure how much time has elapsed
    set_bridge_control(bdf, "0043", "Dell1234")
    set_bridge_control(bdf, "0003", "Dell1234")
    start = time.time()
    while(read_link_status(bdf)[-1] != train_speed and hex_to_binary(read_link_status(bdf))[-9:-4] != train_width):
        pass
    end = time.time()
    train_time = end - start
    return train_time

def main():
    train_times = []
    bdfs = input("Enter BDF numbers (comma separated): ").split(",")
    for bdf in bdfs:
        bdf = bdf.strip()
        for i in range(30):
            train_time = get_train_time(bdf)
            if train_time != -1:
                train_times.append(train_time)
    if train_times:
        max_train_time = max(train_times)
        adjusted_time = max_train_time * 1.2
        print(f"Adjusted Time: {adjusted_time}")
        with open("adjusted_time.txt", "w") as f:
            f.write(str(adjusted_time))
    else:
        print("No valid train times obtained.")

if __name__ == "__main__":
    main()
