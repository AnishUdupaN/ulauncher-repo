import json
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

class GnomeClipboardExtension(Extension):

    def __init__(self):
        super(GnomeClipboardExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument()

        # Construct the path to the Gnome extension's registry.txt
        # Assuming GLib.get_user_cache_dir() is ~/.cache
        gnome_clipboard_history_path = os.path.expanduser(
            '~/.cache/clipboard-indicator@tudmotu.com/registry.txt'
        )

        if not os.path.exists(gnome_clipboard_history_path):
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Gnome Clipboard History Not Found',
                    description='Make sure the Gnome Clipboard Indicator extension is installed and active.',
                    highlightable=False
                )
            ])

        try:
            with open(gnome_clipboard_history_path, 'r') as f:
                registry_content = json.load(f)

            # Filter and sort items (newest first, as per Gnome extension's behavior)
            # The Gnome extension stores newest items at the end of the array, so we reverse it
            # to show newest first in Ulauncher.
            clipboard_history = []
            for entry in reversed(registry_content):
                if entry.get('mimetype', '').startswith('text/') or entry.get('mimetype', '') == 'STRING' or entry.get('mimetype', '') == 'UTF8_STRING':
                    clipboard_history.append(entry)
                # For images, we'll just show a placeholder for now
                elif entry.get('mimetype', '').startswith('image/'):
                    clipboard_history.append({
                        'contents': '[Image]',
                        'mimetype': entry.get('mimetype'),
                        'favorite': entry.get('favorite', False)
                    })

            if not clipboard_history:
                items.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name='Clipboard History is Empty',
                        description='No items found in Gnome Clipboard history.',
                        highlightable=False
                    )
                )
            else:
                for i, entry in enumerate(clipboard_history):
                    content = entry['contents']
                    if query and query.lower() not in content.lower():
                        continue

                    items.append(
                        ExtensionResultItem(
                            icon='images/icon.png',
                            name=content,
                            description=f'Copy to clipboard (Mimetype: {entry["mimetype"]})',
                            highlightable=True,
                            # Pass the content to the ItemEnterEvent for copying
                            on_enter=ExtensionCustomAction({'text': content}, keep_app_open=False)
                        )
                    )

        except json.JSONDecodeError:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Error Reading Clipboard History',
                    description='Could not parse registry.txt. It might be corrupted.',
                    highlightable=False
                )
            ])
        except Exception as e:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='An unexpected error occurred',
                    description=str(e),
                    highlightable=False
                )
            ])

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        data = event.get_data()
        text_to_copy = data.get('text')
        if text_to_copy:
            return CopyToClipboardAction(text_to_copy)
        return RenderResultListAction([])
