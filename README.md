# Modular

Modular is a tool to help Transformice developers code their modules. It allows to write the code split in files as if it was a "normal" program; and it also allows to write and use libraries in a really simple way.

## How it works

Internally, this uses [luacheck](https://github.com/mpeterv/luacheck) and a slightly modified [prepdir](https://github.com/Lautenschlager-id/prepdir), plus a few custom scripts in order to lint the code and bundle it into a single file.
The developer can code normally, using `require` calls and those will be detected and merged into a file that can be loaded in Transformice; maintaining the correct behavior.

## How to use it

First, clone this repository and modify `src/release.lua` and `src/init.lua` at your will.

`bundle-config.lua` contains all the prepdir configuration. It has to return a table and each item in that table is a bundle configuration, and a bundle will be generated per each configuration.

Whenever you commit to your GitHub repository, prepdir will generate all the bundles and luacheck will lint them all. If you've modified `src/release.lua`, the linker will merge each bundle into a single file (one file per bundle) and it will then create a GitHub release, using the value of `version` in your release configuration as the name of the release.

Whenever you call `require`, it has to have the following structure: `[schema+]path`. `schema` defaults to `file`, which tells it to require from a local file in `src`.

If `schema` is `github` or `gist`, it will retrieve the content of the file from a github repository or gist at the moment of building bundles. The only file libraries can access is `src/config.lua` and it is shared between all libraries. In this case, the syntax would be `schema+owner/repo[/path][@branch]`; if `path` is not specified, it defaults to `init`, and if `branch` is not specified, it defaults to `master` in the case of a github repository, or an empty string in the case of a github gist.

## Advantages

- Customizable
- Easy to set up
- Easy to use
- Automatically stay updated with as many lua libraries as you want