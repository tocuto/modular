import os
import re
import requests
import tempfile
from slpp import slpp as lua


github_link = (
	"https://raw.githubusercontent.com/"
	"{owner}/{repo}/{branch}/{file}.lua"
)
gist_link = (
	"https://gist.githubusercontent.com/"
	"{owner}/{repo}/raw/{branch}/{file}.lua"
)
require_exp = r"(require\s*\(?\s*[\"'])(.+?)([\"'])"


def normalize_path(path, repo=None):
	# Normalizes a require path (adds default values and shit)
	if "+" in path:
		schema, path = path.split("+", 1)

		if schema in ("github", "gist"):
			# It is a github link
			branch = "master"

			if "@" in path:
				path, branch = path.rsplit("@", 1)

			elif schema == "gist":
				branch = ""

			if path.count("/") == 0:
				raise Exception("Invalid {} path: {}".format(schema, path))

			path = path.split("/", 2)
			owner, repo_name, file = path.pop(0), path.pop(0), "init"

			if path:
				file = path.pop(0)

			return "{}+{}/{}/{}@{}".format(schema, owner, repo_name, file, branch)

		elif schema == "file":
			# Handle files at the end of the function
			pass

		else:
			raise Exception("Unknown schema: {}".format(schema))

	# If it doesn't have a specified schema, assume it is a file.

	if repo:
		# This comes from a repository, avoid local file access
		if path == "config":
			# Retrieve the same config file for all libarries
			return "file+{}".format(path)

		return "{schema}+{owner}/{repo}/{file}@{branch}".format(
			file=path,
			**repo
		)

	# Just a local file
	return "file+{}".format(path)


def get_content(config, src, path):
	schema, path = path.split("+", 1)

	if schema in ("github", "gist"):
		# Parse path
		path, branch = path.rsplit("@", 1)
		owner, repo_name, file = path.split("/", 2)

		# Request content
		link = gist_link if schema == "gist" else github_link

		r = requests.get(link.format(
			owner=owner, repo=repo_name, branch=branch, file=file
		), stream=True)
		r.raise_for_status() # Raise exception if something went wrong

		# Generate temporary buffer files
		tmp = tempfile._get_default_tempdir()
		candidates = tempfile._get_candidate_names()
		input_file = "{}/{}".format(tmp, next(candidates))
		output_file = "{}/{}".format(tmp, next(candidates))

		# Read stream and pipe it into the buffer
		with open(input_file, "wb") as buff:
			for chunk in r.iter_content(chunk_size=1024):
				buff.write(chunk)

		# Preprocess file
		os.system(
			"lua preprocess.lua --cfg {} --file {} > {}"
			.format(config, input_file, output_file)
		)

		with open(output_file, "r") as buff:
			content = buff.read()[:-1] # Remove last newline

		# Delete buffer files
		os.remove(input_file)
		os.remove(output_file)

		return content

	elif schema == "file":
		with open("{}/{}.lua".format(src, path), "r") as file:
			return file.read()


def scan(config, files, dependencies, src, srcpath, repo=None):
	# Look for require calls in the specified file
	files[srcpath] = content = get_content(config, src, srcpath)
	dependencies.add(srcpath)

	for prefix, inp, suffix in re.findall(require_exp, content):
		# Normalize and replace require() content
		dep = normalize_path(inp, repo)
		if dep != inp:
			# Replace requirement input with the normalized version
			files[srcpath] = files[srcpath].replace(
				"{}{}{}".format(prefix, inp, suffix),
				"{}{}{}".format(prefix, dep, suffix),
				1
			)

		if dep not in dependencies:
			schema, path = dep.split("+", 1)
			if schema in ("github", "gist"):
				# Github repository
				path, branch = path.rsplit("@", 1)
				owner, repo_name, _ = path.split("/", 2)

				scan(config, files, dependencies, src, dep, {
					"schema": schema,
					"owner": owner, "repo": repo_name,
					"branch": branch
				})

			elif schema == "file":
				scan(config, files, dependencies, src, dep, repo)


def link(config, src, dst):
	output = ["--[[ COMPUTER GENERATED FILE: DO NOT MODIFY DIRECTLY ]]--"]

	# Gather files and dependencies
	files, dependencies = {}, set()
	scan(config, files, dependencies, src, "file+init")

	# Append a require mockup, so we can use it inside the script
	with open("basic-require.lua", "r") as file:
		output.extend(line.rstrip() for line in file.readlines())

	for name in dependencies:
		print(name)

		# For every dependency, we append their file and use __registerFile()
		# from basic-require.lua; to be able to use it from require()
		output.append(
			'__registerFile("{}", {}, function()'
			.format(name, len(output) + 1)
		)
		output.extend(files.pop(name).split("\n"))
		output.append('end)')

	# Add a call to run init.lua
	output.extend((
		'local done, result = pcall(require, "file+init")',
		'if not done then',
		'	error(__errorMessage(result))',
		'end'
	))
	# Remove trailing whitespace and join all lines
	output = "\n".join(line.rstrip() for line in output)

	# Write to output
	with open(dst, "w") as file:
		file.write(output)


src, dst = "./release", "./dist"
os.mkdir(dst)
# For every release created by preprocess.lua, we link the files
# ./releases/debug/* -> ./dist/debug.lua
for release in os.listdir(src):
	link(
		release,
		"{}/{}".format(src, release),
		"{}/{}.lua".format(dst, release)
	)

# Read release version and show it to the current github workflow
with open("./src/release.lua", "r") as file:
	info = lua.decode(file.read().replace("return ", "", 1))

print(
	"::set-output name=version::v{}".format(info["version"])
)