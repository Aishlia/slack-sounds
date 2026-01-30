import binascii
import struct
import sys
import os
import shutil

def crc(d):
	return struct.pack("<I", binascii.crc32(d))

def x(d):
	return binascii.unhexlify(d.replace(" ",""))

if len(sys.argv) != 2:
	print("ERROR: python3 {} NEW_SOUND_FILE.mp3".format(sys.argv[0]))
	sys.exit(1)

print("[-] Searching for Slack dir")
dir_slack = None
dir_1 = os.path.expanduser('~') + "/Library/Application Support/Slack/Cache/Cache_Data"
dir_2 = os.path.expanduser('~') + "/Library/Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack/Cache/Cache_Data"
is_dir_1_exists = os.path.exists(dir_1)
if not is_dir_1_exists:
	is_dir_2_exists = os.path.exists(dir_2)
	if not is_dir_2_exists:
		print("ERROR: NO ACTIVE SLACK DIR!")
		sys.exit(1)
	else:
		dir_slack = dir_2
		dir_slack_root = os.path.expanduser('~') + "/Library/Containers/com.tinyspeck.slackmacgap/Data/Library/Application Support/Slack"
else:
	dir_slack = dir_1
	dir_slack_root = os.path.expanduser('~') + "/Library/Application Support/Slack"

print("[-] Slack dir found at '{}'".format(dir_slack))
print("[-] Searching for hummus sound cache file")

command_grep = os.popen("grep -ir hummus-200e354.mp3 \"{}\"".format(dir_slack) + "/*_s") # example: 13f007daa736b6cb_s
command_grep_output = command_grep.read()

if not command_grep_output or not "matches" in command_grep_output:
	print("ERROR: No Hummus sound cache file! Go to Slack-->Preferences-->Notifications-->Select Hummus, then close Slack and try again")
	sys.exit(1)

hummus_sound_cache_filename = command_grep_output.split("Cache_Data/")[1].split(" matches")[0]
hummus_sound_cache_filepath = dir_slack + "/" + hummus_sound_cache_filename
print("[-] Found hummus sound cache file '{}'".format(hummus_sound_cache_filename))

#req_resource = "1/0/" + "https://a.slack-edge.com/bv1-9/hummus-200e354.mp3" # previous was bv1-9
req_resource = "1/0/" + "https://a.slack-edge.com/bv1-13/hummus-200e354.mp3" # bv1-10 <--- looks like this number changes with updates..
new_sound_file = sys.argv[1]
new_file_data = open(new_sound_file, "rb").read()
print("[-] Overwriting cache file '{}' with '{}'".format(hummus_sound_cache_filepath, new_sound_file))

new_cache_data = b""
new_cache_data += x("30 5C 72 A7 1B 6D FB FC 09 00 00 00") 	# magic
new_cache_data += struct.pack("<I", len(req_resource)) 		# resource path len
new_cache_data += crc(b"") + b"\x00\x00\x00\x00"			# ?
new_cache_data += req_resource.encode()						# requested resource
new_cache_data += x("6B 67 53 65 01 BF 97 EB 00 00 00 00 00 00 00 00") # magic ?
new_cache_data += struct.pack("<I", len(new_file_data)) + b"\x00\x00\x00\x00" 		# resource len
new_cache_data += crc(new_file_data) + b"\x00\x00\x00\x00" 	# resource len
new_cache_data += new_file_data

with open(hummus_sound_cache_filepath, "wb") as f:
	f.write(new_cache_data)

print("[-] Cache file updated successfully")

# Clear Service Worker cache
service_worker_cache_dir = dir_slack_root + "/Service Worker/CacheStorage"
if os.path.exists(service_worker_cache_dir):
	print("[-] Found Service Worker cache directory")
	
	# Find hummus references in Service Worker cache
	command_grep_sw = os.popen("find \"{}\" -type f -exec grep -l 'hummus' {{}} \\; 2>/dev/null".format(service_worker_cache_dir))
	sw_files = command_grep_sw.read().strip().split('\n')
	sw_files = [f for f in sw_files if f]  # Remove empty strings
	
	if sw_files:
		print("[-] Found {} Service Worker cache files containing hummus references".format(len(sw_files)))
		print("[-] Clearing Service Worker cache to force refresh...")
		
		try:
			# Remove the entire CacheStorage directory
			shutil.rmtree(service_worker_cache_dir)
			print("[-] Service Worker cache cleared successfully")
			print("[!] IMPORTANT: Service Worker cache will be rebuilt when Slack restarts")
		except Exception as e:
			print("[!] Warning: Could not clear Service Worker cache: {}".format(e))
			print("[!] You may need to manually clear it or the sound might not work for notifications")
else:
	print("[-] No Service Worker cache found (this is OK)")

print("\n[-] DONE! Please do the following:")
print("    1. Make sure Slack is completely closed")
print("    2. Restart Slack") 
print("    3. Go to Preferences-->Notifications and select Hummus")
print("    4. The custom sound should now work for both settings preview AND actual notifications!") 