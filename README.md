open the scrip enter in 

DEVICE_ID = ""
IP_ADDRESS = ""
LOCAL_KEY = "

this can be obtained from the [tuya developers portal ](https://auth.tuya.com/?from=https%3A%2F%2Fauth.tuya.com%2Flogin%2Fsilent%3Ffrom%3Dhttps%253A%252F%252Fwww.tuya.com%252Fredirect%253Furl%253Dhttps%253A%252F%252Fplatform.tuya.com)

1) obtain device ID - login to your Tuya account  > cloud > project ( you may need to make one ) > devices 
2) obtain the local key - cloud > API explorer > device management > query device details > key should be listed 
3) ip address - anyway you can ( log into your router )

Usage: Run the file for interactive input (e.g., python3 bulb.py). The same commands can also be passed as arguments (e.g., python3 bulb.py temp 1000).
