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


def getDirectoryPresentation(files, currentDir, showDirsBeforeFiles=True):
    files.sort()
    dirs = []
    filesOnly = []
    for file in files:
        if os.path.isdir(currentDir + os.sep + file):
            # appending trailing os.sep to directories
            directoryPresentation = file + os.sep
            if showDirsBeforeFiles:
                # Showing dirs before files
                dirs.append(directoryPresentation)
            else:
                filesOnly.append(directoryPresentation)
        else:
            filesOnly.append(file)
    files = dirs + filesOnly
    return files


class ScratchSuggestionsList:
    HEADER_LINES = 3  # predefined amount of header lines

    def __init__(self, owner, dirs_first):
        self.showDirsBeforeFiles = dirs_first
        self.scratch_buffer = None
        self.owner = owner
        EventListener.subscribe(self)

    def on_selection_modified(self, view):
        if view == self.scratch_buffer:
            window = self.owner.window
            region = view.sel()[0]
            row, col = view.rowcol(region.a)
            headerLines = ScratchSuggestionsList.HEADER_LINES
            index = math.floor((row - headerLines) * self.num_cols +
                               col/self.col_width)
            if index >= 0 and index < len(self.files):
                sublime.status_message("row: %s col %s, index %s fileName: %s" % (row, col, index, self.files[index]))
                filePath = self.currentDir + os.sep + self.files[index]
                self.owner.on_file_selected(filePath)

    def clear(self):
        if self.scratch_buffer:
            self.scratch_buffer.run_command('clear_file_list')

    def close(self):
        if self.scratch_buffer:
            window = self.owner.window
            window.focus_view(self.scratch_buffer)
            if self.scratch_buffer.id() == window.active_view().id():
                window.run_command('close')
            self.scratch_buffer = None

    def generateNamesTable(self, files, view_width_chars):
        num_files = len(files)

        # getting maximum file name length in list
        maxFileNameLen = len(max(files, key=len))

        col_width = maxFileNameLen + 5

        num_cols = int(view_width_chars / col_width)

        # Store information about colums to use in on_selection_modified
        self.col_width = col_width
        self.num_cols = num_cols

        if num_files > 0:
            buffer_text = ""

            i = 0
            for file in files:
                buffer_text += "".join(file.ljust(col_width))
                i += 1
                if i >= num_cols:
                    buffer_text = buffer_text.strip() + '\n'
                    i = 0
        else:
            buffer_text = "No files found in current directory"

        # strip spaces of last element (if there is)
        buffer_text = buffer_text.strip()
        return buffer_text

    def set_content(self, files, currentDir):
        # sorting entries
        files = getDirectoryPresentation(files,
                                         currentDir,
                                         self.showDirsBeforeFiles)

        # Store files and currentDir, to use in on_selection_modified
        self.files = files
        self.currentDir = currentDir

        if not self.scratch_buffer:
            # create scratch file list if it doesn't already exist
            self.scratch_buffer = self.owner.window.new_file()
            self.scratch_buffer.set_scratch(True)
        else:
            # clear contents of existing scratch list
            self.clear()

        vp_extent = self.scratch_buffer.viewport_extent()
        line_width = self.scratch_buffer.em_width()
        view_width_chars = int(vp_extent[0] / line_width)

        buffer_text = self.generateNamesTable(files, view_width_chars)
        strings = buffer_text.split('\n')
        prefix = "Possible completions found: %d" % len(files)
        maxStringLen = max(len(prefix), len(max(strings, key=len)))
        str_delim = '-' * maxStringLen
        buffer_text = "\n%s\n%s\n%s" \
            % (prefix, str_delim, buffer_text)
        self.scratch_buffer.run_command(
            'show_file_list', {'bufferText': buffer_text})

        # Sublime Text 4 (4094) leaves scratch_buffer focused after update
        # Sublime Text 3 - not
        self.owner.window.focus_view(self.owner._ip)


class StatusSuggestionsList:
    def __init__(self, owner, dirs_first):
        self.showDirsBeforeFiles = dirs_first
        pass

    def clear(self):
        pass

    def close(self):
        pass

    def set_content(self, filesInDir, currentDir):
        filesInDir = getDirectoryPresentation(
            filesInDir,
            currentDir,
            self.showDirsBeforeFiles)
        statusText = ''.join((f + ', ') for f in filesInDir)
        statusText = statusText[:-2]
        statusText = '{ ' + statusText + ' }'
        sublime.status_message(statusText)


class QuickPanelSuggestionsList:
    def __init__(self, owner, dirs_first):
        self.showDirsBeforeFiles = dirs_first
        self.quick_panel = None
        self.owner = owner

    def clear(self):
        pass

    def close(self):
        pass

    def quick_panel_on_close(self, selectedIndex):
        if selectedIndex == -1:
            self.setCurrentIndex(-1)
            self.owner.window.focus_view(self.owner._ip)
        else:
            self.owner.on_file_selected(self.getFileNameByIndex(selectedIndex))

    def getFileNameByIndex(self, index):
        text = self.currentDir + os.sep
        if index != -1:
            text += self.files[index]
        return text

    def setCurrentIndex(self, currentIndex):
        text = self.getFileNameByIndex(currentIndex)
        self.owner._ip.run_command('update_input_panel', {'text': text})

    def quick_panel_on_highlited(self, selectedIndex):
        self.setCurrentIndex(selectedIndex)

    def set_content(self, files, currentDir):
        self.currentDir = currentDir
        files = getDirectoryPresentation(files,
                                         currentDir,
                                         self.showDirsBeforeFiles)
        self.files = files
        self.owner.window.show_quick_panel(
            [file for file in files],
            self.quick_panel_on_close,
            0,
            0,
            self.quick_panel_on_highlited)
        self.setCurrentIndex(0)


class FilePromptCommand(sublime_plugin.WindowCommand):
    SUGGS_SCRATCH = 0
    SUGGS_STATUS = 1
    SUGGS_QUICK_PANEL = 2

    def show_prompt(self,
                    save_file,
                    suggestions_list_type,
                    dirs_first):
        if suggestions_list_type == FilePromptCommand.SUGGS_SCRATCH:
            self.suggs_list = ScratchSuggestionsList(self, dirs_first)
        elif suggestions_list_type == FilePromptCommand.SUGGS_STATUS:
            self.suggs_list = StatusSuggestionsList(self, dirs_first)
        elif suggestions_list_type == FilePromptCommand.SUGGS_QUICK_PANEL:
            self.suggs_list = QuickPanelSuggestionsList(self, dirs_first)

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

    def on_file_selected(self, filename):
        self._ip.run_command('update_input_panel', {'text': filename})
        # returning focus to input panel
        self.on_done_open(filename)
        self.window.focus_view(self._ip)
        if not os.path.isdir(filename):
            self.window.run_command("hide_panel", {"cancel": True})

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
                    self.suggs_list.set_content(filesInDir, currentDir)

                    prefix = os.path.commonprefix(filesInDir)
                    lowerFiles = [x.lower() for x in filesInDir]
                    caseInsensitivePrefix = os.path.commonprefix(lowerFiles)
                    # For case-insensitive FS (for simplicity, for Windows now,
                    # case-sensitive commonprefix could return less common
                    # part, then real
                    if os.name == 'nt':
                        if len(prefix) < len(caseInsensitivePrefix):
                            prefix = caseInsensitivePrefix
                    newPath = os.path.join(currentDir, prefix)
                else:
                    newPath = os.path.join(currentDir, filesInDir[0])
            else:
                newPath = currentFilePath
                sublime.status_message(
                     'No files match "%s"' % currentFile)
                self.suggs_list.clear()

            if os.path.isdir(newPath) and matchCount == 1:
                if newPath[-1:] != os.sep:
                    newPath += os.sep
            # if currentFilePath != newPath:
            self._ip.run_command('update_input_panel', {'text': newPath})

    def on_done_open(self, text):
        self.suggs_list.close()

        text = os.path.expanduser(text)

        # If we ended up opening directory, do nothing
        if os.path.isdir(text):
            return

        if not os.path.exists(text):
            # 'touch' file if it doesn't exist
            try:
                f = open(text, 'w')
                f.close()
            except IOError:
                sublime.status_message('Unable to create file "[%s]"' % text)

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
        self.suggs_list.close()
        self.save_file_to_disk(text)

    def on_panel_closed(self):
        self.suggs_list.close()

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


class ClearFileListCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.set_read_only(False)
        self.view.erase(edit, sublime.Region(0, self.view.size()))


class ShowFileListCommand(sublime_plugin.TextCommand):
    def run(self, edit, bufferText):
        self.view.insert(edit, 0, bufferText)
        selection = self.view.sel()
        selection.clear()
        selection.add(sublime.Region(0))
        self.view.set_read_only(True)


class UpdateInputPanelCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        allTextRegion = self.view.full_line(0)
        self.view.replace(
            edit,
            allTextRegion,
            text
        )
        selection = self.view.sel()
        selection.clear()
        selection.add(sublime.Region(len(text)))


class OpenFilePrompt(FilePromptCommand):
    def run(self,
            suggestions_list_type=FilePromptCommand.SUGGS_SCRATCH,
            directories_first=True):
        self.show_prompt(
            save_file=False,
            suggestions_list_type=suggestions_list_type,
            dirs_first=directories_first)


class SaveFilePrompt(FilePromptCommand):
    def run(self,
            suggestions_list_type=FilePromptCommand.SUGGS_SCRATCH,
            directories_first=True):
        self.show_prompt(
            save_file=True,
            suggestions_list_type=suggestions_list_type,
            dirs_first=directories_first)


class EventListener(sublime_plugin.EventListener):
    subscribers = list()

    def subscribe(obj):
        EventListener.subscribers.append(obj)

    def on_selection_modified(self, view):
        for sub in EventListener.subscribers:
            if sub is not None:
                sub.on_selection_modified(view)
