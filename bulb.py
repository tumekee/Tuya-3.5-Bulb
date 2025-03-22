import tinytuya
import time
import logging
import json
import colorsys
import sys

# Configure logging for debugging output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Device configuration
DEVICE_ID = ""
IP_ADDRESS = ""
LOCAL_KEY = ""

# Create a BulbDevice instance and set the protocol version
try:
    device = tinytuya.BulbDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
    device.set_version(3.5)
    logging.debug("Created device instance with ID: %s", DEVICE_ID)
except Exception as e:
    logging.error("Failed to create device instance: %s", e)
    exit(1)

# Predefined RGB values (if needed for future functions)
COLOUR_OPTIONS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "pink": (255, 192, 203),
    "white": (255, 255, 255)
}

# Preset hue values for common colours (for the "colour" command)
PRESET_HUES = {
    "red": 0,
    "orange": 30,
    "yellow": 60,
    "green": 120,
    "cyan": 180,
    "blue": 240,
    "purple": 300,
    "pink": 350
}

def parse_colour_hex(hex_str):
    """Parse a 12-character hex string into an HSV dictionary."""
    if len(hex_str) != 12:
        raise ValueError("Unexpected hex colour length")
    hue = int(hex_str[0:4], 16)
    sat = int(hex_str[4:8], 16)
    val = int(hex_str[8:12], 16)
    return {"h": hue, "s": sat, "v": val}

def format_hsv_to_hex(h, s, v):
    """Convert integer HSV values into a 12-character hex string (each as 4-digit hex)."""
    return f"{h:04x}{s:04x}{v:04x}"

def get_current_hsv():
    """
    Retrieve current HSV data from the device status.
    First, try to parse JSON from the "colour_data_v2" key.
    If that fails, try to parse DP "24" as a 12-character hex string.
    Returns an HSV dictionary or None if not found.
    """
    status = device.status()
    logging.debug("Current status: %s", status)
    hsv_data = None
    if "dps" in status:
        if "colour_data_v2" in status["dps"]:
            try:
                hsv_data = json.loads(status["dps"]["colour_data_v2"])
                return hsv_data
            except Exception as e:
                logging.debug("Error parsing JSON from 'colour_data_v2': %s", e)
        if "24" in status["dps"]:
            try:
                hsv_data = parse_colour_hex(status["dps"]["24"])
                return hsv_data
            except Exception as e:
                logging.debug("Error parsing hex from DP '24': %s", e)
    return None

def print_menu():
    print("\nCommands:")
    print("  on         - Turn the bulb on")
    print("  off        - Turn the bulb off")
    print("  temp       - Set white temperature (DP 23; auto-switches to white mode)")
    print("  bright     - Set brightness (10 to 1000)")
    print("  hue        - Update only the hue value")
    print("  sat        - Update only the saturation value")
    print("  colour     - Set a preset hue (common colours)")
    print("  status     - Show current bulb status")
    print("  help       - Display this menu")
    print("  exit       - Quit the program")

def set_white_temp():
    """
    Set the white temperature (DP 23).
    Temperature typically ranges from 0 (warm) to 1000 (cool).
    This command automatically sets DP 21 to "white".
    """
    try:
        temp = int(input("Enter white temperature (0 to 1000): "))
        if not (0 <= temp <= 1000):
            print("Temperature out of range.")
            return
        device.set_value("21", "white")
        time.sleep(0.5)
        device.set_value("23", temp)
        time.sleep(0.5)
        print(f"White temperature set to {temp}.")
    except Exception as e:
        print("Error setting white temperature:", e)

def set_brightness():
    try:
        val = int(input("Enter brightness (10 to 1000): "))
        if val < 10 or val > 1000:
            print("Value out of range.")
            return
        logging.debug("Setting brightness to %d", val)
        response = device.set_brightness(val)
        logging.debug("Response from set_brightness: %s", response)
        print(f"Brightness set to {val}.")
    except Exception as e:
        logging.error("Error setting brightness: %s", e)
        print("Error setting brightness:", e)

def update_hue():
    """
    Update only the hue component.
    Retrieves current HSV data, updates the hue, converts updated HSV to RGB,
    then sends the new colour command. Ensures the bulb is in colour mode.
    """
    try:
        new_hue = int(input("Enter new hue (0 to 360): "))
        if not (0 <= new_hue <= 360):
            print("Hue out of range.")
            return

        hsv_data = get_current_hsv()
        if hsv_data is None:
            print("No HSV data found in status. Using default saturation and brightness (1000 each).")
            hsv_data = {"h": new_hue, "s": 1000, "v": 1000}
        else:
            hsv_data["h"] = new_hue

        # Ensure the device is in colour mode.
        if device.status()["dps"].get("21") != "colour":
            device.set_value("21", "colour")
            time.sleep(0.5)

        h = hsv_data["h"] / 360.0
        s = hsv_data["s"] / 1000.0
        v = hsv_data["v"] / 1000.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        print(f"Updated HSV: {hsv_data} converted to RGB: ({r}, {g}, {b})")
        device.set_colour(r, g, b)
        time.sleep(1)
        print(f"Hue updated to {new_hue}.")
    except Exception as e:
        print("Error updating hue:", e)

def update_saturation():
    """
    Update only the saturation component.
    Retrieves current HSV data, updates the saturation, converts updated HSV to RGB,
    then sends the new colour command. Ensures the device is in colour mode.
    """
    try:
        new_sat = int(input("Enter new saturation (0 to 1000): "))
        if not (0 <= new_sat <= 1000):
            print("Saturation out of range.")
            return

        hsv_data = get_current_hsv()
        if hsv_data is None:
            print("No HSV data found in status. Using default hue 0 and brightness 1000.")
            hsv_data = {"h": 0, "s": new_sat, "v": 1000}
        else:
            hsv_data["s"] = new_sat

        if device.status()["dps"].get("21") != "colour":
            device.set_value("21", "colour")
            time.sleep(0.5)

        h = hsv_data["h"] / 360.0
        s = hsv_data["s"] / 1000.0
        v = hsv_data["v"] / 1000.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        print(f"Updated HSV: {hsv_data} converted to RGB: ({r}, {g}, {b})")
        device.set_colour(r, g, b)
        time.sleep(1)
        print(f"Saturation updated to {new_sat}.")
    except Exception as e:
        print("Error updating saturation:", e)

def preset_colour():
    """
    Display preset hue values for common colours.
    The user selects a preset; update only the hue using that preset,
    leaving the saturation and brightness unchanged.
    """
    print("Available preset hues:")
    for name, hue in PRESET_HUES.items():
        print(f"  {name} : hue {hue}")
    choice = input("Enter preset name: ").strip().lower()
    if choice not in PRESET_HUES:
        print("Unknown preset.")
        return
    preset_hue_value = PRESET_HUES[choice]

    hsv_data = get_current_hsv()
    if hsv_data is None:
        print("No HSV data found in status; using default saturation and brightness (1000 each).")
        hsv_data = {"h": preset_hue_value, "s": 1000, "v": 1000}
    else:
        hsv_data["h"] = preset_hue_value

    if device.status()["dps"].get("21") != "colour":
        device.set_value("21", "colour")
        time.sleep(0.5)

    h = hsv_data["h"] / 360.0
    s = hsv_data["s"] / 1000.0
    v = hsv_data["v"] / 1000.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    print(f"Preset '{choice}' selected. Updated HSV: {hsv_data} converted to RGB: ({r}, {g}, {b})")
    device.set_colour(r, g, b)
    time.sleep(1)
    print(f"Preset hue for '{choice}' applied.")

def get_status():
    try:
        logging.debug("Requesting device status")
        status = device.status()
        logging.debug("Device status: %s", status)
        print("Current Bulb Status:")
        print(status)
    except Exception as e:
        logging.error("Error retrieving status: %s", e)
        print("Error retrieving status:", e)

def process_command(cmd, args):
    """Process a command from the command line."""
    if cmd == "on":
        device.turn_on()
        print("Bulb turned on.")
    elif cmd == "off":
        device.turn_off()
        print("Bulb turned off.")
    elif cmd == "temp":
        try:
            temp = int(args[0])
            device.set_value("21", "white")
            time.sleep(0.5)
            device.set_value("23", temp)
            time.sleep(0.5)
            print(f"White temperature set to {temp}.")
        except Exception as e:
            print("Error setting white temperature:", e)
    elif cmd == "bright":
        try:
            val = int(args[0])
            device.set_brightness(val)
            print(f"Brightness set to {val}.")
        except Exception as e:
            print("Error setting brightness:", e)
    elif cmd == "hue":
        try:
            new_hue = int(args[0])
            hsv_data = get_current_hsv()
            if hsv_data is None:
                hsv_data = {"h": new_hue, "s": 1000, "v": 1000}
            else:
                hsv_data["h"] = new_hue
            if device.status()["dps"].get("21") != "colour":
                device.set_value("21", "colour")
                time.sleep(0.5)
            h = hsv_data["h"] / 360.0
            s = hsv_data["s"] / 1000.0
            v = hsv_data["v"] / 1000.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            device.set_colour(r, g, b)
            time.sleep(1)
            print(f"Hue updated to {new_hue}.")
        except Exception as e:
            print("Error updating hue:", e)
    elif cmd == "sat":
        try:
            new_sat = int(args[0])
            hsv_data = get_current_hsv()
            if hsv_data is None:
                hsv_data = {"h": 0, "s": new_sat, "v": 1000}
            else:
                hsv_data["s"] = new_sat
            if device.status()["dps"].get("21") != "colour":
                device.set_value("21", "colour")
                time.sleep(0.5)
            h = hsv_data["h"] / 360.0
            s = hsv_data["s"] / 1000.0
            v = hsv_data["v"] / 1000.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            device.set_colour(r, g, b)
            time.sleep(1)
            print(f"Saturation updated to {new_sat}.")
        except Exception as e:
            print("Error updating saturation:", e)
    elif cmd == "colour":
        try:
            preset_name = args[0].lower()
            if preset_name not in PRESET_HUES:
                print("Unknown preset.")
                return
            preset_hue_value = PRESET_HUES[preset_name]
            hsv_data = get_current_hsv()
            if hsv_data is None:
                hsv_data = {"h": preset_hue_value, "s": 1000, "v": 1000}
            else:
                hsv_data["h"] = preset_hue_value
            if device.status()["dps"].get("21") != "colour":
                device.set_value("21", "colour")
                time.sleep(0.5)
            h = hsv_data["h"] / 360.0
            s = hsv_data["s"] / 1000.0
            v = hsv_data["v"] / 1000.0
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
            device.set_colour(r, g, b)
            time.sleep(1)
            print(f"Preset hue for '{preset_name}' applied.")
        except Exception as e:
            print("Error updating preset hue:", e)
    elif cmd == "status":
        print(device.status())
    else:
        print("Unknown command.")

if __name__ == "__main__":
    # If command-line arguments are provided, process them and exit.
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        args = sys.argv[2:]
        process_command(cmd, args)
    else:
        # Otherwise, run in interactive mode.
        print("Connecting to the Tuya Smart Bulb...")
        print_menu()
        while True:
            command = input("\nEnter command: ").strip().lower()
            if command == "on":
                try:
                    logging.debug("Turning bulb on")
                    response = device.turn_on()
                    logging.debug("Response from turn_on: %s", response)
                    print("Bulb turned on.")
                except Exception as e:
                    logging.error("Error turning bulb on: %s", e)
                    print("Error turning bulb on:", e)
            elif command == "off":
                try:
                    logging.debug("Turning bulb off")
                    response = device.turn_off()
                    logging.debug("Response from turn_off: %s", response)
                    print("Bulb turned off.")
                except Exception as e:
                    logging.error("Error turning bulb off: %s", e)
                    print("Error turning bulb off:", e)
            elif command == "temp":
                set_white_temp()
            elif command == "bright":
                set_brightness()
            elif command == "hue":
                update_hue()
            elif command == "sat":
                update_saturation()
            elif command == "colour":
                preset_colour()
            elif command == "status":
                get_status()
            elif command == "help":
                print_menu()
            elif command == "exit":
                print("Exiting...")
                break
            else:
                print("Unknown command. Type 'help' to see available commands.")
