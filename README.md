# subl-open-file-prompt

Sublime Text 3 plugin, which implements 'Linux-styled' file open and save prompt with suggestions.

Improvements of prompt\_open\_file\_path.py from [cg-sublime](https://github.com/loquens/cg-sublime) by [Chris Guilbeau](https://forum.sublimetext.com/u/chrisguilbeau).

## Usage

### Installation

Put _subl-open-file-prompt_ directory inside _Packages_ directory of Sublime Text, which could be located by selecting "_Preferences - Browse Packages..._" command from Sublime Text menu.

### Keybindings

Suggested keybindings:

    { "keys": ["ctrl+o"], "command": "open_file_prompt" },
    { "keys": ["ctrl+shift+s"], "command": "save_file_prompt" },

It is possible to add one or more arguments for both commands. For example:

    { "keys": ["ctrl+o"], "command": "open_file_prompt", "args": { "suggestions_list_type": 0, "directories_first" : true } }

Values for _suggestions\_list\_type_:
 * 0 - scratch buffer (default)
 * 1 - status line
 * 2 - quick panel

Values for _directories\_first_:
 * true - show directories before files in suggestions list (default)
 * false - show files and directories in alphabetical order