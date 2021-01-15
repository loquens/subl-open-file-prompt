import sublime
import sublime_plugin
import os
import math


def getHomeDir():
    return os.getenv('HOME') or os.getenv("USERPROFILE")


def fileNameStartsWith(fileName, prefix):
    if os.name == 'nt':
        return fileName.lower().startswith(prefix.lower())
    return fileName.startswith(prefix)


class FilePromptCommand(sublime_plugin.WindowCommand):
    def show_prompt(self, save_file, use_scratch_buffer):
        self.showDirsBeforeFiles = True
        self.scratch_file_list = None
        self.use_scratch_buffer = use_scratch_buffer

        currentDir = self.getStartDir()
        if save_file:
            promptText = "Save file:"
            doneCallback = self.on_done_save
        else:
            promptText = "Open file:"
            doneCallback = self.on_done_open
        self._ip = self.window.show_input_panel(
            promptText,
            currentDir,
            doneCallback,
            self.on_change,
            self.on_panel_closed
        )

    def getStartDir(self):
        startDir = getHomeDir() + os.sep
        activeView = self.window.active_view()
        if activeView:
            currentFilePath = activeView.file_name()
            if currentFilePath:
                startDir = os.path.dirname(currentFilePath) + os.sep
        return startDir

    def on_change(self, text):
        if not text:
            return

        text = os.path.expanduser(text)

        pos = text.find('\t')
        if pos != -1:
            currentFilePath = text.replace('\t', '')
            currentFile = os.path.basename(currentFilePath)
            currentDir = os.path.dirname(currentFilePath)
            filesInDir = [
                fileName
                for fileName in os.listdir(currentDir)
                if fileNameStartsWith(fileName, currentFile)
            ]

            matchCount = 0
            if filesInDir:
                matchCount = len(filesInDir)
                if matchCount > 1:
                    if self.use_scratch_buffer:
                        self.set_scratch_file_list(filesInDir, currentDir)
                    else:
                        statusText = ''.join((f + ', ') for f in filesInDir)
                        statusText = statusText[:-2]
                        statusText = '{ ' + statusText + ' }'
                        sublime.status_message(statusText)

                    prefix = os.path.commonprefix(filesInDir)
                    lowerFiles = [x.lower() for x in filesInDir]
                    caseInsensitivePrefix = os.path.commonprefix(lowerFiles)
                    # For case-insensitive FS (for simplicity, for Windows now,
                    # case-sensitive commonprefix could return less common
                    # part, then real
                    if os.name == 'nt':
                        if len(prefix) < len(caseInsensitivePrefix):
                            prefix = caseInsensitivePrefix
                    sublime.status_message('prefix: ' + prefix)
                    newPath = os.path.join(currentDir, prefix)
                else:
                    newPath = os.path.join(currentDir, filesInDir[0])
            else:
                newPath = currentFilePath
                sublime.status_message(
                     'No files match "%s"' % currentFile)
                self.file_list_clear()

            if os.path.isdir(newPath) and matchCount == 1:
                if newPath[-1:] != os.sep:
                    newPath += os.sep
            self._ip.run_command('update_input_panel', {'text': newPath})

    def on_done_open(self, text):
        self.close_scratch_list()

        text = os.path.expanduser(text)

        # If we ended up opening directory, do nothing
        if os.path.isdir(text):
            return

        if not os.path.exists(text):
            # 'touch' file if it doesn't exist
            try:
                try:
                    f = open(text, 'w')
                finally:
                    f.close()
            except IOError:
                self.message('Unable to create file "[%s]"' % text)

        try:
            self.window.open_file(text)
            numGroups = self.window.num_groups()
            currentGroup = self.window.active_group()
            if currentGroup < numGroups - 1:
                newGroup = currentGroup + 1
            else:
                newGroup = 0
            self.window.run_command("move_to_group", {"group": newGroup})
        except Exception:
            sublime.status_message('Unable to open "%s"' % text)

    def on_done_save(self, text):
        self.close_scratch_list()
        self.save_file_to_disk(text)

    def on_panel_closed(self):
        self.close_scratch_list()

    def save_file_to_disk(self, file_name):
        window = self.window
        view = window.active_view()

        if view.is_dirty():
            view.set_scratch(True)

        file_contents = self.get_view_content()

        try:
            f = open(file_name, "wb")
            try:
                f.write(file_contents)
            finally:
                f.close()
        except IOError:
            self.message('Unable to write file "[%s]"' % file_name)

        (group, index) = window.get_view_index(view)

        window.focus_view(view)
        window.run_command('close')
        try:
            new_view = window.open_file(file_name)
            window.set_view_index(new_view, group, index)
        except Exception:
            sublime.status_message(
                'Unable to open written file "%s"' % file_name)

    def get_view_content(self):
        view = self.window.active_view()

        # Get the default encoding from the settings
        encoding = view.encoding()
        if encoding == 'Undefined':
            encoding = 'UTF-8'

        # Get the correctly encoded contents of the view
        input_text = view.substr(sublime.Region(0, view.size()))
        file_contents = input_text.encode(encoding)
        return file_contents

    def set_scratch_file_list(self, files, currentDir):
        if not self.scratch_file_list:
            # create scratch file list if it doesn't already exist
            self.scratch_file_list = self.window.new_file()
            self.scratch_file_list.set_scratch(True)
        else:
            # clear contents of existing scratch list
            self.file_list_clear()

        num_files = len(files)

        # sorting entries
        files.sort()

        vp_extent = self.scratch_file_list.viewport_extent()
        line_height = self.scratch_file_list.line_height()
        line_width = self.scratch_file_list.em_width()
        view_height_chars = int(math.floor(vp_extent[1] / line_height))
        view_width_chars = int(vp_extent[0] / line_width)

        dirs = []
        filesOnly = []
        for file in files:
            if os.path.isdir(currentDir + os.sep + file):
                # appending trailing os.sep to directories
                directoryPresentation = file + os.sep
                if self.showDirsBeforeFiles:
                    # Showing dirs before files
                    dirs.append(directoryPresentation)
                else:
                    filesOnly.append(directoryPresentation)
            else:
                filesOnly.append(file)
        files = dirs + filesOnly

        # getting maximum file name length in list
        maxFileNameLen = len(max(files, key=len))

        col_width = maxFileNameLen + 5

        num_cols = int(view_width_chars / col_width)

        if num_files > 0:
            buffer_text = ""

            i = 0
            for file in files:
                buffer_text += "".join(file.ljust(maxFileNameLen+1))
                i += 1
                if i >= num_cols:
                    buffer_text = buffer_text.strip() + '\n'
                    i = 0
        else:
            buffer_text = "No files found in current directory"

        # strip spaces of last element (if there is)
        buffer_text = buffer_text.strip()

        strings = buffer_text.split('\n')
        prefix = "Possible completions found: %d" % num_files
        maxStringLen = max(len(prefix), len(max(strings, key=len)))
        str_delim = '-' * maxStringLen
        buffer_text = "\n%s\n%s\n%s" \
            % (prefix, str_delim, buffer_text)
        self.scratch_file_list.run_command(
            'show_file_list', {'bufferText': buffer_text})

        # Sublime Text 4 (4094) leaves scratch_file_list focused after update
        # Sublime Text 3 - not
        self.window.focus_view(self._ip)

    def close_scratch_list(self):
        if self.scratch_file_list:
            self.window.focus_view(self.scratch_file_list)
            if self.scratch_file_list.id() == self.window.active_view().id():
                self.window.run_command('close')

    def file_list_clear(self):
        if self.scratch_file_list is not None:
            self.scratch_file_list.run_command('clear_file_list')

class ClearFileListCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.set_read_only(False)
        self.view.erase(edit, sublime.Region(0, self.view.size()))


class ShowFileListCommand(sublime_plugin.TextCommand):
    def run(self, edit, bufferText):
        self.view.insert(edit, 0, bufferText)
        self.view.set_read_only(True)


class UpdateInputPanelCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        allTextRegion = self.view.full_line(0)
        self.view.replace(
            edit,
            allTextRegion,
            text
        )


class OpenFilePrompt(FilePromptCommand):
    def run(self, use_scratch_buffer=True):
        self.show_prompt(
            save_file=False,
            use_scratch_buffer=use_scratch_buffer)


class SaveFilePrompt(FilePromptCommand):
    def run(self, use_scratch_buffer=True):
        self.show_prompt(
            save_file=True,
            use_scratch_buffer=use_scratch_buffer)
