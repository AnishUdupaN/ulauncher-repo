import os
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

class FileSearchExtension(Extension):
    def __init__(self):
        super(FileSearchExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())

class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        items = []
        query = event.get_argument() or ""
        search_path = os.path.expanduser(extension.preferences.get('search_path', '~'))

        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Search for files and folders',
                    description='Type a query to search for files and folders',
                    on_enter=None
                )
            ])

        results = self.run_search(query, search_path)

        for result in results[:15]:
            is_dir = os.path.isdir(result)
            items.append(
                ExtensionResultItem(
                    icon='images/folder.png' if is_dir else 'images/file.png',
                    name=os.path.basename(result),
                    description=result,
                    on_enter=OpenAction(result),
                    on_alt_enter=CopyToClipboardAction(result)
                )
            )

        return RenderResultListAction(items)

    def run_search(self, search_term, search_dir):
        try:
            # Try with 'fdfind'
            output = subprocess.check_output(['fdfind', search_term, search_dir], text=True)
        except FileNotFoundError:
            # Fallback to 'fd'
            try:
                output = subprocess.check_output(['fd', search_term, search_dir], text=True)
            except FileNotFoundError:
                return [] # Silently fail for the extension
        except subprocess.CalledProcessError:
            return []
        return output.strip().split('\n')

if __name__ == '__main__':
    FileSearchExtension().run()