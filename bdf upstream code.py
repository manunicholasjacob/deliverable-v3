
def gpu_traverse_up():
    # use nvidia-smi to get all the BDF of the GPUs
    bdf_read = execute_shell_command("nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader")
    bdf_read = bdf_read.split('\n')
    bdf_read = [":".join(line.split(':')[1:]) for line in bdf_read]
    gpu_bdf_list = [bdf.lower() for bdf in bdf_read]
    # get a list of all bdfs
    all_bdf_list = get_bdf_list()

    #get a list of all bdfs with header type 1
    header_bdf_list = [bdf for bdf in all_bdf_list if get_header_type(bdf).startswith("01")]

    physical_slot_numbers = []
    root_ports = []

    for i, gpu_bdf in enumerate(gpu_bdf_list):
        # get the bus for the gpu to compare to secondary bus number
        current_bus = gpu_bdf.split(":")[0]
        current_bdf = gpu_bdf
        port_found = False
        root_port_found = False
        # print(f"starting {i} GPU")

        # keep traversing up the tree until a valid physical port number is found
        while(not port_found and not root_port_found):
            # print(f"current bus: {current_bus}")
            upstream_connection = None

            # find the bdf with a secondary bus of our current bus
            for bdf in header_bdf_list:
                if get_secondary_bus_number(bdf) == current_bus:
                    upstream_connection = bdf 

            # if no upstream connection is found, we are at the root port, report and add to list
            if upstream_connection is None:
                # print(f"did not find a port with secondary bus as {current_bus}")
                root_port_found = True
                root_ports.append(current_bdf)
                break
            else:
                # print("Upstream Connection: " + f"{upstream_connection}")
                slot_capabilities = read_slot_capabilities(upstream_connection)
                # Extract the physical slot number from slot capabilities bits [31:19]
                # Convert from hex to binary to decimal
                slot_number = int(hex_to_binary(slot_capabilities)[:13], 2)

                # print(f"slot_number: {slot_number}")

            # We only want relevant physical ports to our system, in this case 21 to 29
            if(slot_number in range(21,29) and port_found is False):
                physical_slot_numbers.append(slot_number)
                port_found = True
            current_bdf = upstream_connection
            current_bus = upstream_connection.split(":")[0]
        
        # if a valid physical port was not found, report
        if(not port_found):
            physical_slot_numbers.append(-1)
    # gpu_streams = {gpuBDF : [physical_slot_numbers[i], root_ports[i]] for i, gpuBDF in enumerate(gpu_bdf_list)}
    gpu_streams = [[gpuBDF, physical_slot_numbers[i], root_ports[i]] for i, gpuBDF in enumerate(gpu_bdf_list)]
    return gpu_streams
