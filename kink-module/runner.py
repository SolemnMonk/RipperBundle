import time, os.path, subprocess, re, multiprocessing, threading, json, shutil

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import manifest

class Runner:
	@classmethod
	def run(self, args, credentials):
		urls = []
		type = None
		types = manifest.Manifest.types

		if args.type in [types[0], types[1]]:
			type = "performer"
			for id in args.ids:
				urls.append(id)
		elif args.type in [types[2], types[3]]:
			type = "channel"
			for name in args.names:
				urls.append(name)
		elif args.type in [types[4], types[5]]:
			type = "shoot"
			for url in args.urls:
				urls.append(url)

		un = credentials["username"]
		pw = credentials["password"]

		# username, password, dir, process_limit, urls, type, 
		# 	quality, trailer, photos, clips, join
		processed_args = (un, pw, args.dir, args.processes, urls, type, 
			args.quality, args.trailer, args.photos, args.clips, args.join)

		k = Kink(*processed_args)
		k.startup()
		start = time.time()
		k.rip()
		k.shutdown()

		if(args.display_stats):
			end = time.time()
			duration = end - start
			minutes = duration // 60
			seconds = str(int(duration % 60)).zfill(2)
			hours = str(int(minutes // 60)).zfill(2)
			minutes = str(int(minutes % 60)).zfill(2)
			print(f"Time taken (hh:mm:ss): {hours}:{minutes}:{seconds}")

class Kink:
	driver = None
	photo_dispatcher_thread = None
	trailer_dispatcher_thread = None
	video_dispatcher_thread = None
	clip_dispatcher_thread = None
	stop_dispatching = False
	
	# The elements in this list are themselves 3 element lists.
	# These 3 elements are [shoot_id, download_command, unzip_command]
	#	shoot_id is a string
	#	download_command is a tuple
	#	unzip_command is a tuple
	photo_argument_lists = []
	
	sites = None

	def __init__(
		self, username="", password="", dir=".", process_limit=4, urls=[], 
		type="shoot", quality="HD", trailer=True, photos=True, clips=False, 
		join=True):
		
		Kink.photo_dispatcher_thread = threading.Thread(
			target=self.__dispatch_photos)
		
		self.username = username
		self.password = password
		self.root_url = "https://www.kink.com/"
		self.dir = dir
		self.process_limit = process_limit
		self.urls = []
		self.type = type
		self.quality = quality
		self.trailer = trailer
		self.photos = photos
		self.clips = clips
		self.join = join
		self.performers_completed = 0
		self.shoots_completed = 0
		self.channels_completed = 0

		for url in urls:
			if type == "performer":
				self.urls.append(self.__build_performer_url(url))
			elif type == "channel":
				self.urls.append(self.__build_channel_url(url))
			else:
				self.urls.append(self.__build_shoot_url(url))
		
		self.__load_sites()

		Kink.photo_dispatcher_thread.start()
		
	def __load_sites(self):
		sites_path = os.path.join(".", "kink-module", "sites.json")
		if os.path.exists(sites_path):
			with open(sites_path) as f:
				self.sites = json.loads(f.read())

	def __dispatch_photos(self):
		print("Beginning photo dispatcher thread...")
		while not Kink.stop_dispatching or len(Kink.photo_argument_lists) != 0:
			if len(Kink.photo_argument_lists) == 0:
				continue

			print("Argument list found! Dispatching...")
			command_list = Kink.photo_argument_lists.pop(0)
			id = command_list[0]
			command_list = command_list[1:]
			aria_command_list = [c[0] for c in command_list]
			_7z_command_list = [c[1] for c in command_list]

			pool = multiprocessing.Pool(self.process_limit)
			
			pool.map(self.download_media, aria_command_list)
			pool.map(self.unzip_media, _7z_command_list)

			zip_paths = [
				os.path.join(c[1][2], c[1][4]) for c in aria_command_list]
			
			for z in zip_paths:
				os.remove(z)

			photo_dir = aria_command_list[0][1][2]

			photo_rename_command = self.build_photo_rename_command(
				photo_dir, id)
			subprocess.run(photo_rename_command)

			self.suction_photos(photo_dir)
				
		print("Exiting photo dispatcher thread...")

	def suction_photos(self, dir, is_prime_invocation=True):
		dirs = []
		files = []

		contents = os.scandir(dir)
		for i in contents:
			if i.is_dir():
				dirs.append(os.path.join(dir, i.name))
			else:
				files.append(os.path.join(dir, i.name))

		if len(dirs) > 0:
			for d in dirs:
				files += self.suction_photos(d, False)
		
		if is_prime_invocation:
			for f in files:
				shutil.move(f, dir)
			for d in dirs:
				shutil.rmtree(d)
			parent = os.path.split(dir)[0]
			os.rename(dir, os.path.join(parent, "Photos"))
		else:
			return files

	def __build_channel_url(self, name):
		return "https://www.kink.com/channel/" + name

	def __build_performer_url(self, id):
		return "https://www.kink.com/model/" + id
	
	def __build_shoot_url(self, url):
		if "kink.com" in url:
			return url
		else:
			return "https://www.kink.com/shoot/" + id

	def startup(self):
		Kink.driver = webdriver.Chrome(
			executable_path=os.path.join("3rd-party-tools", "chromedriver.exe"))
		Kink.driver.maximize_window()
		Kink.driver.implicitly_wait(5)
		Kink.driver.get(self.root_url)
		self.__bypass_splash_screen()
		self.__login()

	def shutdown(self):
		Kink.driver.quit()
	
	def __bypass_splash_screen(self):
		splash_screen_xpath = "//form[@id='contentTypeModal']"
		show_everything_xpath = "//button[@type='submit' and contains(@value,'gay') and contains(@value,'straight')]"

		try:
			Kink.driver.find_element_by_xpath(splash_screen_xpath)
			Kink.driver.find_element_by_xpath(show_everything_xpath).click()
		except:
			print("No splash screen to bypass")
			pass

	def __login(self):
		login_button_xpath = "//a[@id='kBarLogin']"
		login_form_submit_xpath = "//button[@type='submit' and @name='login']"
		username_box_xpath = "//input[@name='username']"
		password_box_xpath = "//input[@name='password']"
		
		Kink.driver.find_element_by_xpath(login_button_xpath).click()
		time.sleep(1)
		Kink.driver.find_element_by_xpath(username_box_xpath).send_keys(
			self.username)
		Kink.driver.find_element_by_xpath(password_box_xpath).send_keys(
			self.password)
		Kink.driver.find_element_by_xpath(login_form_submit_xpath).click()

		time.sleep(5)
		
		while True:
			try:
				# Figure out what's needed for detecting captchas
				break
			except:
				break
		print("No captcha found!")

	def rip(self):
		for url in self.urls:
			Kink.driver.get(url)
			if self.type == "channel":
				print("Channel")
				self.__rip_channel()
			elif self.type == "performer":
				print("Performer")
				self.__rip_performer()
			elif self.type == "shoot":
				print("Single shoot")
				self.__rip_shoot()
		
		Kink.stop_dispatching = True
		Kink.photo_dispatcher_thread.join()
		
		print("Rip completed.")
		print("Total shoots ripped: " + str(self.shoots_completed))
		print("Total channels ripped: " + str(self.channels_completed))
		print("Total performers ripped: " + str(self.performers_completed))

	def __rip_channel(self):
		print("Sorry bro, not done yet.")

	def __rip_performer(self):
		print("Sorry bro, not done yet.")

	def __rip_shoot(self):
		title_xpath = "//h1[@class='shoot-title']"
		performers_xpath = "//span[@class='names']/a"
		tags_xpath = "//p[@class='starring']/a"
		site_xpath = "//div[contains(@class,'shoot-logo')]/a"

		title = self.driver.find_element_by_xpath(title_xpath).text.title()
		performers = self.driver.find_elements_by_xpath(performers_xpath)
		tags = self.driver.find_elements_by_xpath(tags_xpath)

		site = self.driver.find_element_by_xpath(site_xpath).get_attribute(
			"href")
		site = site[site.rindex('/') + 1:]
		site = self.sites[site]

		title = re.subn("", "", title)[0]

		dir_name = os.path.join("Kink", site, title)
		dir_name = re.subn("[<>:\"/\\|?*]", "", dir_name)[0]
		dir_name = re.subn("\\.{3,}", "…", dir_name)[0]
		dir_name = dir_name[:64] if len(dir_name) > 64 else dir_name
		dir_name = os.path.join(self.dir, dir_name)
		
		check = os.path.exists(dir_name)
		
		# if self.trailer:
		# 	self.__save_trailer()
		
		if self.photos:
			self.__save_photos(site, title)

		# if self.clips:
		# 	self.__save_clips()
		# else:
		# 	self.__save_video()
		
		self.shoots_completed += 1

	#(error_strings, command, str(i + 1), url, title, False)
	def download_media(self, args):
		process = subprocess.run(args[1])
		if process.returncode != 0:
			args[0].append("Download failed; command: " + args[1])

	#(error_strings, command, str(i + 1), url, title, False)
	def unzip_media(self, args):
		process = subprocess.run(args[1])
		if process.returncode != 0:
			args[0].append("Unzip failed; command: " + str(args[1]))

	def __save_photos(self, site, title):
		show_zips_xpath = "//a[@class='ziplink']"
		image_zip_link_xpath = "//a[@class='zip-links']"
		
		id = re.match(r"^https?://[a-z.]+/shoot/(\d+)$", 
			self.driver.current_url).group(1)

		self.driver.find_element_by_xpath(show_zips_xpath).click()
		time.sleep(1)

		zips = self.driver.find_elements_by_xpath(image_zip_link_xpath)

		error_strings = []
		
		dir_name = os.path.join("Kink", site, title)
		dir_name = re.subn("[<>:\"/\\|?*]", "", dir_name)[0]
		dir_name = re.subn("\\.{3,}", "…", dir_name)[0]
		dir_name = os.path.join(self.dir, dir_name, "tmp-p")

		args = []
		for i in range(0, len(zips)):
			aria_command_handle = self.build_photo_zip_aria_command(
				zips, i, dir_name, error_strings, site, title)
			_7z_command_handle = self.build_photo_zip_7z_command(
				zips, i, dir_name, error_strings, site, title)
			
			args.append([aria_command_handle, _7z_command_handle])

		Kink.photo_argument_lists.append([id] + args)

	def build_photo_zip_aria_command(self, zips, i, dir_name, error_strings, 
		site, title):
		
		aria_path = os.path.join("3rd-party-tools", "aria2", "aria2c.exe")
		zip = zips[i]
		url = zip.get_attribute("href")
		command = [aria_path, "-d", dir_name, "-o"]
		ext_index = url.rindex(".")
		ext = url[ext_index:ext_index + 4]

		file_name = "z" + str(i + 1).zfill(2) + ext
		
		command.append(file_name)
		command.append(url)

		command_handle = (error_strings, command)
		return command_handle

	def build_photo_zip_7z_command(self, zips, i, dir_name, error_strings, 
		site, title):
		
		_7z_path = os.path.join("3rd-party-tools", "7z.exe")
		zip = zips[i]
		url = zip.get_attribute("href")
		command = [_7z_path, "x"]
		ext_index = url.rindex(".")
		ext = url[ext_index:ext_index + 4]

		intermediate_dir_name = "z" + str(i + 1).zfill(2)

		command.append('-o' + os.path.join(dir_name, intermediate_dir_name))
		command.append(os.path.join(dir_name, intermediate_dir_name) + ext)

		command_handle = (error_strings, command)
		return command_handle

	def build_photo_rename_command(self, dir, id):
		brc_path = os.path.join("3rd-party-tools", "BRC64.exe")
		command = [brc_path, "/NOFOLDERS", "/DIR:" + dir, "/RECURSIVE", 
			f"/FIXEDNAME:Shoot {id} Image ", "/AUTONUMBER:1:1:S::10:3", 
			"/EXECUTE"]
		return command

	def __save_trailer(self):
		trailer_button_xpath = "//div[@class='trailer']"
		print("Pending evaluation")

	def __save_clips(self):
		clips_button_xpath = "//div[@class='clips']"
		clips_categories_xpath = "//ul[contains(@class,'clips') and contains(@class,'open')]/li"
		clips_xpath = "//ul[contains(@class,'clips') and contains(@class,'open')]/li/ul/li/a"
		print("Sorry bro, not done yet.")

	def __join_clips(self):
		pass

	def __save_video(self):
		movie_button_xpath = "//div[@class='full']"
		movie_quality_xpath = "//ul[contains(@class,'full-movie') and contains(@class,'open')]"
		movie_xpath = "//ul[contains(@class,'full-movie') and contains(@class,'open')]/li/a"
		print("Sorry bro, not done yet.")

def print_warning():
	print("This file is meant to be imported by other Python files, not run directly. Exiting now.")

if __name__ == "__main__":
	print_warning()
