import argparse

class Manifest:
	types = ["performer", "p", 
		 	 "channel", "c",
		 	 "shoot", "s"]

	@classmethod
	def get_parser(cls, provided_parser):
		provided_parser.add_argument("-d", "--dir", dest="dir", default="", help="The directory to download to")
		provided_parser.add_argument("-p", "--processes", type=int, dest="processes", default=4, help="The maximum number of processes to run while downloading")
		provided_parser.add_argument("-t", "--type", dest="type", choices=cls.types, required=True, help="The type that the ripper needs to aim for. 'p', 'performer', 'c', and 'channel' take a list of names, while 's' and 'shoot' takes a list of URLs")
		provided_parser.add_argument("-q", "--quality", dest="quality", default="HD", help="Set the quality to download videos at")
		provided_parser.add_argument("-r", "--trailer", dest="trailer", action="store_true", help="If included, the trailers will be downloaded when available")
		provided_parser.add_argument("-o", "--photos", dest="photos", action="store_true", help="If included, photosets will be downloaded when available")
		provided_parser.add_argument("-c", "--clips", dest="clips", action="store_true", help="If included, clips will be downloaded instead of the big video file")
		provided_parser.add_argument("-j", "--join", dest="join", action="store_true", help="If included, clips will be joined to form a single video (has no effect if '-c' is not set")
		provided_parser.add_argument("-s", "--display_stats", dest="display_stats", action="store_true", help="Display timing statistics after the process ends")

		group = provided_parser.add_mutually_exclusive_group(required=True)
		group.add_argument("-n", "--name", dest="names", nargs=argparse.REMAINDER, help="The names to rip for channels")
		group.add_argument("-i", "--ids", dest="ids", nargs=argparse.REMAINDER, help="The names to rip for performers")
		group.add_argument("-u", "--url", dest="urls", nargs=argparse.REMAINDER, help="The URLs to rip for shoots")
		
	alias = ["k", "kink"]
	friendly_name = "Kink"
	credential_key = "kink"
