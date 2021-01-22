# subl-open-file-prompt

Sublime Text 3 plugin, which implements 'Linux-styled' file open and save prompt with suggestions and autocompletion by 'Tab' key.

It has three different types of suggestions list (configurable in keyboard shortcut):
 * scratch buffer
    * matched files and dirs displayed in columns in scratch buffer
    * files could be selected by mouse also
 * status bar
    * matched files and dirs displayed only in status bar
 * quick panel
    * matched files and directories displayed in quick panel

Basic idea and source for improvements was taken from prompt\_open\_file\_path.py from [cg-sublime](https://github.com/loquens/cg-sublime) by [Chris Guilbeau](https://forum.sublimetext.com/u/chrisguilbeau).

## Usage

### Installation

#### From Package control

It is preffered way of installation.
 * Install [Package control](https://packagecontrol.io/installation) package.
 * Go to _Preferences - "Package Control" - "Install Package" - FilePrompt_, and press Enter.

#### From source
Clone git repository and put _subl-open-file-prompt_ directory inside _Packages_ directory of Sublime Text, which could be located by selecting "_Preferences - Browse Packages..._" command from Sublime Text menu.

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

### Changelog

* 0.0.9
    * input panel does not need "tab_completions" set to "False" in settings to work correctly
* 0.0.8
    * (scratch) added ability to open file/select directory by mouse click
    * small improvements and bug fixes
* 0.0.1 to 0.0.7
    * implementation steps
