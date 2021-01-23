-- Configuration for bundles (preprocess)

return {
	{
		name = "debug",
		vars = {
			DEBUG = true,
		}
	},
	{
		name = "production",
		vars = {
			DEBUG = false,
		}
	}
}