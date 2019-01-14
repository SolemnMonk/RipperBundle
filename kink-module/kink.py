import time, subprocess, os.path, re, multiprocessing, threading, json
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class Kink:
	driver = None
	dispatcher_thread = None
	argument_lists = []
	stop_dispatching = False
	
	sites = None

	def __init__(self, exec_dir, username, password, dir, process_limit, urls, type, quality, trailer, photos, clips, join):
		Kink.dispatcher_thread = threading.Thread(target=self.__dispatch)
		
		self.username = username
		self.password = password
		self.root_url = "https://www.kink.com/"
		self.dir = dir
		self.exec_dir = exec_dir
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

		if type == "performer":
			for url in urls:
				self.urls.append(self.__build_performer_url(url))
		if type == "channel":
			for url in urls:
				self.urls.append(self.__build_channel_url(url))
		else:
			for url in urls:
				self.urls.append(self.__build_shoot_url(url))
		
		self.__load_sites()

		#Kink.dispatcher_thread.start()
		
	def __load_sites(self):
		sites_path = os.path.join(self.exec_dir, "kink_module", "sites.json")
		if os.path.exists(sites_path):
			with open(sites_path) as f:
				Kink.sites = json.loads(f.read())

	def __dispatch(self):
		print("Beginning dispatcher thread...")
		while not Kink.stop_dispatching or len(Kink.argument_lists) != 0:
			if len(Kink.argument_lists) != 0:
				print("Argument list found! Dispatching...")
				argument_list = Kink.argument_lists.pop(0)

				pool = multiprocessing.Pool(self.process_limit)
				
				pool.map(self.download_image, argument_list)
				
		print("Exiting dispatcher thread...")
		
	def startup(self):
		Kink.driver = webdriver.Chrome(executable_path=os.path.join(os.path.abspath(self.exec_dir), "dependencies", "chromedriver.exe"))
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
			pass

	def __login(self):
		login_button_xpath = "//a[@id='kBarLogin']"
		login_form_submit_xpath = "//button[@type='submit' and @name='login']"
		username_box_xpath = "//input[@name='username']"
		password_box_xpath = "//input[@name='password']"
		
		Kink.driver.find_element_by_xpath(login_button_xpath).click()
		time.sleep(1)
		Kink.driver.find_element_by_xpath(username_box_xpath).send_keys(self.username)
		Kink.driver.find_element_by_xpath(password_box_xpath).send_keys(self.password)
		Kink.driver.find_element_by_xpath(login_form_submit_xpath).click()

		time.sleep(5)
		
		flag = False;
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
				from . import kink_channel
				kink_channel.rip(url, self, Kink.driver)
				self.__rip_channel()
			elif self.type == "performer":
				print("Performer")
				from . import kink_performer
				kink_performer.rip(url)
				self.__rip_performer()
			elif self.type == "shoot":
				print("Single shoot")
				from . import kink_shoot
				kink_shoot.rip(url)
				self.__rip_shoot()
		
		Kink.stop_dispatching = True
		#Kink.dispatcher_thread.join()
		
		print("Rip completed.")
		print("Total shoots ripped: " + str(self.shoots_completed))
		print("Total channels ripped: " + str(self.channels_completed))
		print("Total performers ripped: " + str(self.performers_completed))

	def __rip_channel(self):
		print("Sorry bro, not done yet.")

	def __rip_performer(self):
		print("Sorry bro, not done yet.")

	def __rip_all(self, type_xpath):
		time_period_xpath = "//li[@class='dropdown'][3]//ul/li/a[text() = '" + self.time_period + "']"
		girl_name_xpath = "//article/header//h2/a"
		load_more_xpath = "//a[@id='load-more']"
		
		choice = Kink.driver.find_element_by_xpath(type_xpath)
		Kink.driver.get(choice.get_attribute("href"))
		
		choice = Kink.driver.find_element_by_xpath(time_period_xpath)
		Kink.driver.get(choice.get_attribute("href"))
		
		girls = []
		
		iteration = 0
		while True:
			iteration += 1
			names = Kink.driver.find_elements_by_xpath(girl_name_xpath)
			for name in names:
				girls.append(name.text)
			if iteration > 1:
				Kink.driver.execute_script("for(i=0;i<24;i++) {e = document.evaluate(\"//article[1]\", document.documentElement); e = e.iterateNext(); if (e == null) {break;}e.parentNode.removeChild(e);}")
				time.sleep(2)
			lmb = Kink.driver.find_elements_by_xpath(load_more_xpath)
			if len(lmb) > 0 and lmb[0].is_displayed():
				lmb[0].click()
				time.sleep(10)
			else:
				break

		girls = list(set(girls))
		
		for girl in sorted(girls):
			url = self.__build_url(girl)
			Kink.driver.get(url)
			self.__rip_girl()
		
	def __rip_girl(self):
		load_more_xpath = "//a[@id='load-more']"
		photos_xpath = "//div[@id='content-container']//a[text()='Photos']"
		photosets_xpath = "//div[@id='content-container']//a[text()='Photosets']"
		set_title_xpath = "//article/header//h2/a"
		
		url = Kink.driver.find_element_by_xpath(photos_xpath).get_attribute("href")
		Kink.driver.get(url)
		url = Kink.driver.find_element_by_xpath(photosets_xpath).get_attribute("href")
		Kink.driver.get(url)
	
		set_links = []
		
		iteration = 0
		while True:
			iteration += 1
			titles = Kink.driver.find_elements_by_xpath(set_title_xpath)
			for title in titles:
				set_links.append(title.get_attribute("href"))
			if iteration > 1:
				Kink.driver.execute_script("for(i=0;i<9;i++) {e = document.evaluate(\"//article[1]\", document.documentElement); e = e.iterateNext(); if (e == null) {break;}e.parentNode.removeChild(e);}")
				time.sleep(2)
			lmb = Kink.driver.find_elements_by_xpath(load_more_xpath)
			if len(lmb) > 0 and lmb[0].is_displayed():
				lmb[0].click()
				time.sleep(10)
			else:
				break
			
		set_links = list(set(set_links))
		
		for link in set_links:
			Kink.driver.get(link)
			self.__rip_set()
			
		self.girls_completed += 1
		
	def __download_and_save_set(self, urls, girl, title):
		aria_path = os.path.join(self.exec_dir, "dependencies", "aria2", "aria2c.exe")
		error_strings = []
		
		dir_name = os.path.join("Suicide Girls", girl.title(), title.title())
		dir_name = re.subn("[<>:\"/\|?*]", "", dir_name)[0]
		dir_name = re.subn("\\.{3,}", "…", dir_name)[0]
		dir_name = os.path.join(self.dir, dir_name)

		args = []
		for i in range (0, len(urls)):
			command = [aria_path, "-d", dir_name, "-o"]

			ext = urls[i][urls[i].rindex("."):]
			file_name = "Suicide Girls - " + girl.title() + " - " + title.title() + " - Img" + str(i + 1).zfill(3) + ext
			file_name = re.subn("[<>:\"/\|?*]", "", file_name)[0]
			file_name = re.subn("\\.{3,}", "…", file_name)[0]

			if os.path.exists(dir_name + file_name):
				continue

			command.append(file_name)
			command.append(urls[i])
			
			args.append((error_strings, command, str(i + 1), urls[i], girl, title))
		
		Kink.argument_lists.append(args)
		
		if len(error_strings) > 0:
			f = open(os.path.join(dir_name, "errors.txt", "w"))
			f.write("\n".join(sorted(error_strings)))
			f.close()
		
	def __build_channel_url(self, name):
		return "https://www.kink.com/channel/" + name

	def __build_performer_url(self, id):
		return "https://www.kink.com/model/" + id
	
	def __build_shoot_url(self, url):
		if "kink.com" in url:
			return url
		else:
			return "https://www.kink.com/shoot/" + id

	def start_processes(async_result):
		async_result.get()
		
def print_warning():
	print("This file is meant to be imported by other Python files, not run directly. Exiting now.")

if __name__ == "__main__":
	print_warning()
