import argparse, sys, os.path, time, json
from suicidegirls_module.suicidegirls import SuicideGirls

username = None
password = None

def print_welcome():
	print("Suicide girls")

def load_credentials(exec_dir):
	credentials_path = os.path.join(exec_dir, "credentials.json")
	if os.path.exists(credentials_path):
		with open(credentials_path) as f:
			credentials = json.loads(f.read())
			
			global username
			global password
			
			if username is None and "username" in credentials.keys():
				username = credentials["username"]
			if password is None and "password" in credentials.keys():
				password = credentials["password"]

def parse_arguments():
	parser = build_argparse()
	args = parser.parse_args()
	
	urls = []
	type = None
	
	if args.type in [types[0], types[1]]:
		type = "girl"
		for name in args.names:
			urls.append(name)
	elif args.type in [types[2], types[3]]:
		type = "hopeful"
		for name in args.names:
			urls.append(name)
	elif args.type in [types[4], types[5]]:
		type = "set"
		for url in args.urls:
			urls.append(url)
	elif args.type in [types[6], types[7]]:
		type = "girls"
		urls = ["https://www.suicidegirls.com/photos/"]
	elif args.type in [types[8], types[9]]:
		type = "hopefuls"
		urls = ["https://www.suicidegirls.com/photos/"]
	elif args.type in [types[10], types[11], types[12]]:
		type = "sotds"
		urls = ["https://www.suicidegirls.com/photos/"]
	elif args.type in [types[13], types[14]]:
		type = "all"
		urls = ["https://www.suicidegirls.com/photos/"]
	
	if username is None:
		un = args.un
	else:
		un = username
	if password is None:
		pw = args.pw
	else:
		pw = password
	
	return args.dir, args.processes, urls, type, time_period_translations[args.time_period], un, pw
	
def build_argparse(parser):
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-d", "--dir", dest="dir", default="", help="The directory to download files to")
	parser.add_argument("-p", "--processes", type=int, dest="processes", default=4, help="The maximum number of processes to run while downloading")
	parser.add_argument("-t", "--type", dest="type", choices=types, help="The type that the ripper needs to aim for. 'g', 'girl' 'h', and 'hopeful' take a list of names, 'set' takes a list of URLs, and the 'all_' options (and their shortened synonyms) take no further arguments. The 'all_' options are used to select the filter for the main photos page, they are equivalent to 'girl' with the full list of names for that filter")
	parser.add_argument("-i", "--in", dest="time_period", choices=time_periods, default=time_periods[0], help="The time period to filter the 'all_' types to")
	parser.add_argument("-n", "--name", dest="names", nargs=argparse.REMAINDER, help="The names to rip for girls and hopefuls")
	parser.add_argument("-u", "--url", dest="urls", nargs=argparse.REMAINDER, help="The URLs to rip for sets")
	
	if username is None:
		parser.add_argument("-l", "--username", dest="un", default=None, help="The username to use when logging in")
	if password is None:
		parser.add_argument("-s", "--password", dest="pw", default=None, help="The password to use when logging in")
	
	return parser
	
if __name__ == "__main__":
	print_welcome()
	exec_dir = os.path.dirname(os.path.abspath(__file__))
	load_credentials(exec_dir)
	args = parse_arguments()
	sg = SuicideGirls(exec_dir, args[5], args[6], args[0], args[1], args[2], args[3], args[4])
	sg.startup()
	start = time.time()
	sg.rip()
	sg.shutdown()
	end = time.time()
	duration = end - start
	seconds = duration % 60
	minutes = duration // 60
	hours = minutes // 60
	minutes = minutes % 60
	print("Time taken (hh:mm:ss): " + str(int(hours)).zfill(2) + ":" + str(int(minutes)).zfill(2) + ":" + str(int(seconds)).zfill(2))
