

import logging
import os
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

logger = logging.getLogger(__name__)


class FindFileExtension(Extension):

    def __init__(self):
        super(FindFileExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        query = event.get_argument()
        if not query:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                  name='Enter search query',
                                  on_enter=DoNothingAction())
            ])

        search_dir = os.path.expanduser(extension.preferences.get('search_path', '~'))
        try:
            # We are using "fdfind" as command, but it can be "fd" in some systems.
            # We will check for both.
			
            command = ['fdfind', query, search_dir]
            try:
                output = subprocess.check_output(command, text=True)
            except FileNotFoundError:
                command = ['fd', query, search_dir]
                output = subprocess.check_output(command, text=True)
				
            results = output.strip().split('\n')

            items = []
            for result in results[:15]:
                if os.path.isdir(result):
                    icon = 'images/folder.png'
                else:
                    icon = 'images/file.png'

                items.append(
                    ExtensionResultItem(icon=icon,
                                      name=os.path.basename(result),
                                      description=result,
                                      on_enter=OpenAction(result)))
            return RenderResultListAction(items)
        except FileNotFoundError:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                  name='`fd` or `fdfind` command not found',
                                  description='Please install it to use this extension',
                                  on_enter=DoNothingAction())
            ])
        except subprocess.CalledProcessError:
            return RenderResultListAction([
                ExtensionResultItem(icon='images/icon.png',
                                  name='No results found',
                                  on_enter=DoNothingAction())
            ])


if __name__ == '__main__':
    FindFileExtension().run()
