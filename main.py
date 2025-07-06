import json
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction


class ClipboardHistoryExtension(Extension):

    def __init__(self):
        super(ClipboardHistoryExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(PreferencesEvent, PreferencesEventListener())
        self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())


class PreferencesEventListener(EventListener):
    def on_event(self, event, extension):
        extension.preferences.update(event.preferences)


class PreferencesUpdateEventListener(EventListener):
    def on_event(self, event, extension):
        extension.preferences[event.id] = event.new_value


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []
        query = event.get_argument() or ""

        home_dir = os.path.expanduser("~")
        registry_path = os.path.join(home_dir, ".cache", "clipboard-indicator@tudmotu.com", "registry.txt")

        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return RenderResultListAction([
                ExtensionResultItem(name="Error",
                                    description="Could not read or find clipboard history file.",
                                    on_enter=HideWindowAction())
            ])

        filtered_data = []
        for item in data:
            content = item.get("contents", "").strip()
            if query.lower() in content.lower():
                filtered_data.append(item)

        # Sort by last used timestamp
        filtered_data.sort(key=lambda x: x.get('used', 0), reverse=True)

        num_entries = int(extension.preferences.get('num_entries', 10))

        for item in filtered_data:
            content = item.get("contents", "").strip()
            lines = content.split('\n')
            if len(lines) > 4:
                content = '\n'.join(lines[:4]) + '...'

            items.append(ExtensionResultItem(
                name=content,
                description="Press Enter to copy",
                on_enter=CopyToClipboardAction(item.get("contents", "").strip())
            ))

        return RenderResultListAction(items[:num_entries])


if __name__ == '__main__':
    ClipboardHistoryExtension().run()
