import argparse

class Manifest:
	types = ["girl", "g", 
			 "hopeful", "h", 
			 "set", "s", 
			 "all_girls", "ag", 
			 "all_hopefuls", "ah",
			 "all_sets_of_the_day", "all_sotds", "as",
			 "all", "a"]
	time_periods = ["all",
					"24hours",
					"7days",
					"1month",
					"3months",
					"6months"] + [str(x) for x in range(2001, 2019)]
	time_period_translations = {**{time_periods[0] : "All Time",
								   time_periods[1] : "24 Hours",
								   time_periods[2] : "7 Days",
								   time_periods[3] : "1 Month",
								   time_periods[4] : "3 Months",
								   time_periods[5] : "Six Months"},
								**{x : x for x in time_periods[6:]}}

	def get_parser(provided_parser):
		provided_parser.add_argument("-d", "--dir", dest="dir", default="", help="The directory to download files to")
		provided_parser.add_argument("-p", "--processes", type=int, dest="processes", default=4, help="The maximum number of processes to run while downloading")
		provided_parser.add_argument("-t", "--type", dest="type", choices=types, help="The type that the ripper needs to aim for. 'g', 'girl' 'h', and 'hopeful' take a list of names, 'set' takes a list of URLs, and the 'all_' options (and their shortened synonyms) take no further arguments. The 'all_' options are used to select the filter for the main photos page, they are equivalent to 'girl' with the full list of names for that filter")
		provided_parser.add_argument("-i", "--in", dest="time_period", choices=time_periods, default=time_periods[0], help="The time period to filter the 'all_' types to")
		provided_parser.add_argument("-n", "--name", dest="names", nargs=argparse.REMAINDER, help="The names to rip for girls and hopefuls")
		provided_parser.add_argument("-u", "--url", dest="urls", nargs=argparse.REMAINDER, help="The URLs to rip for sets")
		
	alias = ["sg", "sgirls", "suicidegirls"]
	credential_key = "sg"
