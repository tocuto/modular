-- require mockup
local require, __registerFile, __errorMessage
do
	local files = {}
	local lines = {}
	local loaded = {}

	function __registerFile(name, line, callback)
		-- Register a file and the starting line
		files[name] = callback
		lines[#lines + 1] = {line, name}
	end

	function __errorMessage(msg)
		-- Return an error message that specifies the file and the local line
		local line, desc = string.match(msg, "^[^:]+:(%d+): (.*)$")
		if not line then return msg end

		line = tonumber(line)

		local file = "?.lua"
		local marker
		for i = #lines, 1, -1 do
			marker = lines[i]

			if marker[1] <= line then
				file = marker[2]
				line = line - marker[1]
				break
			end
		end

		return file .. ":" .. line .. ": " .. desc
	end

	function require(file)
		-- Load a file and cache it
		if not loaded[file] then
			loaded[file] = files[file]()
		end
		return loaded[file]
	end
end