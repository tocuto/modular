local lfs = require("lfs")
local Processor = require("./prepdir/prepdir")


local function prepdir(content, settings)
	local processor = Processor:new(content)
	processor.envTbl = setmetatable({}, {__index = settings})
	return processor:execute()
end


local generate
function generate(settings, src, dest)
	-- Preprocess a file from src and send the output to dest, recursive.
	lfs.mkdir(dest)

	for file in lfs.dir(src) do
		if file ~= "." and file ~= ".." then
			local source = src .. "/" .. file
			local destination = dest .. "/" .. file

			if lfs.attributes(source).mode == "directory" then
				-- If it is a directory, we do this again
				generate(settings, source, destination)

			else
				-- Preprocess file
				local content = io.open(source):read("*a")

				local f = io.open(destination, "w")
				f:write(prepdir(content, settings))
				f:flush()
			end
		end
	end
end


local config = require("bundle-config")

if #arg == 0 then -- default behavior
	local src, release = "./src", "./release"
	lfs.mkdir(release)

	-- Preprocess the code with every possible configuration
	release = release .. "/"
	for i = 1, #config do
		generate(config[i].vars, src, release .. config[i].name)
	end

else -- preprocess specific file with specific config
	local cfg, file
	for i = 1, #arg, 2 do
		if arg[i] == "--cfg" then
			cfg = arg[i + 1]
		elseif arg[i] == "--file" then
			file = arg[i + 1]
		end
	end

	assert(cfg and file, "missing arguments")

	local found = false
	for i = 1, #config do
		if config[i].name == cfg then
			local content = io.open(file):read("*a")
			print(prepdir(content, config[i].vars))

			found = true
			break
		end
	end

	assert(found, "unknown configuration")
end