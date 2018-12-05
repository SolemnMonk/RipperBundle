import os, os.path, importlib, argparse, sys, json
#operations to add: install module, install dependency, list aliases, resolve conflicts, add credentials

credentials = {}

def cd():
	script_dir = os.path.abspath(os.path.dirname(__file__))
	os.chdir(script_dir)

def get_module_manifest(module_dir):
	module = importlib.import_module(module_dir + ".manifest")
	return getattr(module, "Manifest")

def get_module_runner(module_dir):
	module = importlib.import_module(module_dir + ".runner")
	return getattr(module, "Runner")

def get_potential_modules():
	files = os.listdir(".")
	
	potential_modules = []
	for file in files:
		if os.path.isdir(file):
			potential_modules.append(file)
	
	return potential_modules

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

def get_module_dirs(potential_modules):
	modules = []
	for pm in potential_modules:
		contents = os.listdir("./" + pm)
		if "__init__.py" not in contents:
			continue
		if "manifest.py" not in contents:
			continue
		if "runner.py" not in contents:
			continue
		
		manifest = get_module_manifest(pm)
		if not is_valid_manifest(manifest):
			continue
		
		runner = get_module_runner(pm)
		if not is_valid_runner(runner):
			continue
		
		modules.append(pm)
	return modules

def get_aliases(module_dirs):
	aliases = {}
	conflicts = {}
	for module_dir in module_dirs:
		manifest = get_module_manifest(module_dir)
		for alias in set(manifest.alias):
			if alias in aliases.keys():
				cs = conflicts.get("alias", [])
				if len(cs) is 0:
					cs.append(aliases[alias])
				cs.append(module_dir)
				conflicts[alias] = cs
				continue
			aliases[alias] = module_dir
	return aliases, conflicts

def print_alias_conflicts(conflicts):
	if len(conflicts) > 0:
		print("Alias conflicts discovered, please resolve them to continue.")
		for alias in conflicts.keys():
			print(f"Alias '{alias}' provided by {', '.join(conflicts[alias])}")

def build_base_parser():
	parser = argparse.ArgumentParser()
	
	parser.add_argument("-l", "--list", help="List the aliases and friendly names for all installed modules", action="store_true", dest="list")
	parser.add_argument("--install-module", help="Install a new module; accepts a path to a directory", dest="install_module")
	parser.add_argument("--install-dependency", help="Install a dependency for a module; accepts a path to a directory or a single file", dest="install_dependency")
	parser.add_argument("--resolve-conflict", help="Resolve all alias conflicts; enters an interactive mode", action="store_true", dest="resolve_conflict")
	parser.add_argument("--add-credentials", help="Add credentials for one or more plugins; enters an interactive mode", action="store_true", dest="credentials")

	return parser

def build_parsers(aliases):
	parser = build_base_parser()
	subparsers = parser.add_subparsers(dest="target_alias", metavar="pluginAlias")

	for alias in aliases:
		manifest = get_module_manifest(aliases[alias])
		sub_parser = subparsers.add_parser(alias)
		manifest.get_parser(sub_parser)
	
	return parser

def dispatch(target_module_dir, args):
	print("args: " + str(args))
	manifest = get_module_manifest(target_module_dir)
	credential_key = manifest.credential_key
	
	runner = get_module_runner(target_module_dir)
	runner.run(args, credentials.get(credential_key))

def load_credentials():
	credentials_path = "credentials.json"
	if os.path.exists(credentials_path):
		global credentials
		
		with open(credentials_path) as f:
			credentials = json.loads(f.read())

def main():
	cd()

	load_credentials()

	potential_modules = get_potential_modules()
	module_dirs = get_module_dirs(potential_modules)

	aliases, conflicts = get_aliases(module_dirs)

	if len(conflicts) > 0:
		print_alias_conflicts(conflicts)
		return
	print("No plugin alias conflicts detected.")

	parsers = build_parsers(aliases)

	args = parsers.parse_args()

	dispatch(aliases[args.target_alias], args)
	
if __name__ == "__main__":
	main()