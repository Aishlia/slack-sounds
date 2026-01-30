import binascii
import struct
import sys
import os
import shutil
import subprocess

def crc(d):
	return struct.pack("<I", binascii.crc32(d))

def x(d):
	return binascii.unhexlify(d.replace(" ",""))

if len(sys.argv) != 2:
	print("ERROR: python3 {} NEW_SOUND_FILE.mp3".format(sys.argv[0]))
	sys.exit(1)

print("Slack Sound Replacement Script v3")
print("=" * 50)

# Check if Slack is running
slack_running = subprocess.run(["pgrep", "-x", "Slack"], capture_output=True).returncode == 0
if slack_running:
	print("ERROR: Slack is currently running. Please quit Slack completely before running this script.")
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

print(f"[+] dir_slack: {dir_slack}")

# Get the sound file path before changing directories
sound_file = os.path.abspath(sys.argv[1])
if not os.path.exists(sound_file):
	print(f"ERROR: Sound file not found: {sound_file}")
	sys.exit(1)

print(f"[+] Using sound file: {sound_file}")

# Clear Service Worker cache
service_worker_dir = os.path.join(dir_slack_root, "Service Worker/CacheStorage")
if os.path.exists(service_worker_dir):
	print("[-] Clearing Service Worker cache...")
	try:
		shutil.rmtree(service_worker_dir)
		os.makedirs(service_worker_dir)
		print("[+] Service Worker cache cleared successfully")
	except Exception as e:
		print(f"[!] Warning: Could not clear Service Worker cache: {e}")
else:
	print("[!] Service Worker cache directory not found")

# Find and modify cache files
os.chdir(dir_slack)
print("[-] Searching for cache files with hummus sound...")

# Search for cache files containing the hummus URL
# Note: The version number in the URL may change with Slack updates
hummus_pattern = b"hummus-200e354.mp3"
cache_files = []

for filename in os.listdir('.'):
	if filename.endswith('_s'):
		try:
			with open(filename, 'rb') as f:
				content = f.read()
				if hummus_pattern in content:
					cache_files.append(filename)
		except:
			pass

if not cache_files:
	print("[!] Warning: No cache files found with hummus sound pattern")
	print("[!] The sound URL pattern may have changed. Searching for alternative patterns...")
	
	# Try alternative patterns
	alt_patterns = [b"hummus", b"/hummus", b"slack-edge.com"]
	for pattern in alt_patterns:
		for filename in os.listdir('.'):
			if filename.endswith('_s'):
				try:
					with open(filename, 'rb') as f:
						content = f.read()
						if pattern in content and filename not in cache_files:
							cache_files.append(filename)
				except:
					pass
	
	if cache_files:
		print(f"[+] Found {len(cache_files)} cache file(s) with alternative patterns")
	else:
		print("[!] No cache files found. The cache structure may have changed.")

# Process each cache file
for cache_file in cache_files:
	print(f"\n[-] Processing cache file: {cache_file}")
	
	with open(cache_file, 'rb') as f:
		data = f.read()
	
	# Find the hummus URL in the data
	url_start = data.find(b"https://a.slack-edge.com/")
	if url_start == -1:
		print(f"[!] Could not find Slack edge URL in {cache_file}")
		continue
	
	# Find the end of the URL
	url_end = data.find(b".mp3", url_start) + 4
	if url_end == 3:  # -1 + 4
		print(f"[!] Could not find .mp3 extension in {cache_file}")
		continue
	
	url = data[url_start:url_end]
	print(f"[+] Found URL: {url.decode('ascii', errors='ignore')}")
	
	# Get the sound file data
	with open(sound_file, 'rb') as f:
		sound_data = f.read()
	
	# Create the replacement data structure
	size_sound = len(sound_data)
	off_to_size = 5 + 4 + len(url) + 5
	header = x("0000000010800000000000")
	data2 = header + struct.pack("<I", size_sound) + url + b"\x30\x00\x00\x00\x00" + sound_data + x("0000")
	c = crc(data2)
	final = c + data2
	
	# Write to file
	output_file = f"{cache_file}_new"
	with open(output_file, 'wb') as f:
		f.write(final)
	
	# Replace the original file
	try:
		shutil.move(output_file, cache_file)
		print(f"[+] Successfully replaced {cache_file}")
	except Exception as e:
		print(f"[!] Error replacing {cache_file}: {e}")

print("\n" + "=" * 50)
print("IMPORTANT: Additional Manual Step Required!")
print("=" * 50)
print("\nSlack also uses a local resource file for notifications that cannot be")
print("automatically replaced due to macOS security restrictions.")
print("\nTo complete the sound replacement, you need to manually replace:")
print(f"/Applications/Slack.app/Contents/Resources/hummus.mp3")
print(f"\nSteps:")
print("1. In Finder, go to Applications")
print("2. Right-click on Slack and select 'Show Package Contents'")
print("3. Navigate to Contents > Resources")
print("4. Find 'hummus.mp3' and rename it to 'hummus.mp3.backup'")
print("5. Copy your custom sound file and rename it to 'hummus.mp3'")
print("6. You may need to enter your password to make these changes")
print("\nAlternatively, you can try this command in Terminal:")
print(f"sudo cp '{sound_file}' /Applications/Slack.app/Contents/Resources/hummus.mp3")
print("\nNote: You'll need to repeat this after Slack updates.")
print("=" * 50) 