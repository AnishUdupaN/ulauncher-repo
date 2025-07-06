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
            # Check if the file is empty before attempting to load JSON
            if os.path.getsize(gnome_clipboard_history_path) == 0:
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name='Clipboard History File Empty',
                        description='The Gnome Clipboard history file is empty.',
                        highlightable=False
                    )
                ])

            with open(gnome_clipboard_history_path, 'r') as f:
                registry_content = json.load(f)

            # Ensure registry_content is a list
            if not isinstance(registry_content, list):
                return RenderResultListAction([
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name='Error Reading Clipboard History',
                        description='Clipboard history file contains malformed data (not a list).',
                        highlightable=False
                    )
                ])

            clipboard_history = []
            for entry in reversed(registry_content):
                if entry.get('mimetype', '').startswith('text/') or entry.get('mimetype', '') == 'STRING' or entry.get('mimetype', '') == 'UTF8_STRING':
                    clipboard_history.append(entry)
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
                            on_enter=ExtensionCustomAction({'text': content}, keep_app_open=False)
                        )
                    )

        except json.JSONDecodeError:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='Error Reading Clipboard History',
                    description='Could not parse registry.txt. It might be corrupted or not valid JSON.',
                    highlightable=False
                )
            ])
        except IOError as e: # Catch specific IO errors like permission denied
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='File Access Error',
                    description=f'Could not read registry.txt: {str(e)}. Check permissions.',
                    highlightable=False
                )
            ])
        except Exception as e:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='An unexpected error occurred',
                    description=f'An unexpected error occurred: {str(e)}',
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
