import os, os.path, importlib, argparse, sys, json, getpass

credentials = {}

def cd():
	script_dir = os.path.abspath(os.path.dirname(__file__))
	os.chdir(script_dir)

def get_plugin_manifest(plugin_dir):
	plugin = importlib.import_module(plugin_dir + ".manifest")
	return getattr(plugin, "Manifest")

def get_plugin_runner(plugin_dir):
	plugin = importlib.import_module(plugin_dir + ".runner")
	return getattr(plugin, "Runner")

def get_potential_plugins():
	files = os.listdir(".")
	
	potential_plugins = []
	for file in files:
		if os.path.isdir(file):
			potential_plugins.append(file)
	
	return potential_plugins

def is_valid_manifest(manifest):
	valid = True
	
	alias = getattr(manifest, "alias", None)
	parser = getattr(manifest, "get_parser", None)
	
	valid = valid and alias is not None
	valid = valid and parser is not None
	valid = valid and callable(parser)
	
	return valid

def is_valid_runner(runner):
	valid = True
	
	run = getattr(runner, "run", None)
	
	valid = valid and run is not None
	valid = valid and callable(run)
	
	return valid

def get_plugin_dirs(potential_plugins):
	plugins = []
	for pm in potential_plugins:
		contents = os.listdir("./" + pm)
		if "__init__.py" not in contents:
			continue
		if "manifest.py" not in contents:
			continue
		if "runner.py" not in contents:
			continue
		
		manifest = get_plugin_manifest(pm)
		if not is_valid_manifest(manifest):
			continue
		
		runner = get_plugin_runner(pm)
		if not is_valid_runner(runner):
			continue
		
		plugins.append(pm)
	return plugins

def get_aliases(plugin_dirs):
	aliases = {}
	conflicts = {}
	for plugin_dir in plugin_dirs:
		manifest = get_plugin_manifest(plugin_dir)
		for alias in set(manifest.alias):
			if alias in aliases.keys():
				cs = conflicts.get("alias", [])
				if len(cs) is 0:
					cs.append(aliases[alias])
				cs.append(plugin_dir)
				conflicts[alias] = cs
				continue
			aliases[alias] = plugin_dir
	return aliases, conflicts

def print_alias_conflicts(conflicts):
	if len(conflicts) > 0:
		print("Alias conflicts discovered, please resolve them to continue.")
		for alias in conflicts.keys():
			print(f"Alias '{alias}' provided by {', '.join(conflicts[alias])}")

def build_base_parser():
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-l", "--list", help="List the aliases and friendly names for all installed plugin", action="store_true", dest="list")
	parser.add_argument("--add-credentials", help="Interactive; add credentials for one or more plugins", action="store_true", dest="add_credentials")
	parser.add_argument("--resolve-conflict", help="Interactive; resolve all alias conflicts", action="store_true", dest="resolve_conflict")
	parser.add_argument("--install-plugin", help="Install a new plugin; accepts a path to a directory or the following archives: *.7z, *.zip, *.rar, *.tar, *.tar.gz", default=None, dest="install_plugin")
	parser.add_argument("--install-dependency", help="Install a dependency for a plugin; if a path delimiter / or \\ is present, this accepts a path to a directory or a single file, otherwise it will attempt to install a Python package through pip", default=None, dest="install_dependency")

	return parser

def build_parsers(aliases):
	parser = build_base_parser()
	subparsers = parser.add_subparsers(dest="target_alias", metavar="plugin_alias")

	for alias in aliases:
		manifest = get_plugin_manifest(aliases[alias])
		sub_parser = subparsers.add_parser(alias)
		manifest.get_parser(sub_parser)
	
	return parser

def dispatch(target_plugin_dir, args):
	print("args: " + str(args))
	manifest = get_plugin_manifest(target_plugin_dir)
	credential_key = manifest.credential_key
	
	runner = get_plugin_runner(target_plugin_dir)
	runner.run(args, credentials.get(credential_key))

def load_credentials():
	credentials_path = "credentials.json"
	if not os.path.exists(credentials_path):
		c = open("credentials.json", "w")
		c.write("{}")
		c.close()
	global credentials
	
	with open(credentials_path) as f:
		credentials = json.loads(f.read())

def should_dispatch_to_plugin(args):
	dispatch = True
	
	dispatch = dispatch and not args.list
	dispatch = dispatch and not args.add_credentials
	dispatch = dispatch and not args.resolve_conflict
	dispatch = dispatch and not args.install_plugin is None
	dispatch = dispatch and not args.install_dependency is None

	return dispatch

def list_aliases(aliases):
	sorted_aliases = {}
	for alias in aliases:
		if aliases[alias] not in sorted_aliases:
			sorted_aliases[aliases[alias]] = []
		sorted_aliases[aliases[alias]].append(alias)

	print()
	print("The following plugins are installed; their aliases are listed after them:")
	for alias in sorted_aliases:
		print("\t" + alias + " : " + ", ".join(sorted_aliases[alias]))

def add_credentials(aliases):
	print()
	print("Which plugin would you like to add credentials for?")
	
	selection = -1
	plugin_dirs = sorted(list(set(aliases.values())))
	while True:
		try:
			i = 1

			print("0: <quit application>")
			for plugin_dir in plugin_dirs:
				print(str(i) + ": " + plugin_dir)
			
			selection = input("> ").strip()
			selection = int(selection)
			if selection < 0 or selection > len(plugin_dirs):
				raise ValueError("Invalid selection")
			break
		except:
			print("Invalid selection, please choose a number between 1 and " + str(len(plugin_dirs)))

	if selection is 0:
		print("Exiting...")
		return
	
	manifest = get_plugin_manifest(plugin_dirs[selection - 1])
	credential_key = manifest.credential_key

	print("Enter the username to add:")
	username = input("> ")
	print("Enter the password:")
	password = getpass.getpass("> ")

	additional_fields = {}
	print("If there are any additional fields you need to add to this credential, you may add them now.")
	while True:
		print("What is the field's name? Enter to skip")
		field_name = input("> ")
		if (field_name == ""):
			break
		print("What is the value for '" + field_name + "'?")
		field_value = input("> ")
		additional_fields[field_name] = field_value

	credential = {"username" : username, "password" : password}
	for field in additional_fields:
		credential[field] = additional_fields[field]

	load_credentials()

	global credentials
	credentials[credential_key] = credential

	credentials_path = "credentials.json"
	with open(credentials_path, "w") as f:
		f.write(json.dumps(credentials, indent=2, sort_keys=True))
	
	with open(credentials_path) as f:
		loaded_credentials = json.loads(f.read())
		print(credentials)
		print(loaded_credentials)
		if loaded_credentials == credentials:
			print("Credential added; exiting...")
		else:
			print("Failed to add credential; exiting...")


def resolve_conflict(aliases):
	pass

def install_plugin(args):
	pass

def install_dependency(args):
	pass

def handle_core_arguments(args, aliases):
	if args.list:
		list_aliases(aliases)
	elif args.add_credentials:
		add_credentials(aliases)
	elif args.resolve_conflict:
		resolve_conflict(aliases)
	elif args.install_plugin is not None:
		install_plugin(args)
	elif args.install_dependency is not None:
		install_dependency(args)

def main():
	cd()

	load_credentials()

	potential_plugins = get_potential_plugins()
	plugin_dirs = get_plugin_dirs(potential_plugins)

	aliases, conflicts = get_aliases(plugin_dirs)

	if len(conflicts) > 0:
		print_alias_conflicts(conflicts)
		return
	print("No plugin alias conflicts detected.")

	parsers = build_parsers(aliases)

	args = parsers.parse_args()

	if (should_dispatch_to_plugin(args)):
		dispatch(aliases[args.target_alias], args)
	else:
		handle_core_arguments(args, aliases)

if __name__ == "__main__":
	main()