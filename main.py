import json
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

class ClipboardHistoryExtension(Extension):

    def __init__(self):
        super(ClipboardHistoryExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
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

        favourites = []
        regular = []

        for item in data:
            content = item.get("contents", "").strip()
            if query.lower() in content.lower():
                if item.get("favorite"):
                    favourites.append(item)
                else:
                    regular.append(item)

        # Sort by last used timestamp
        favourites.sort(key=lambda x: x.get('used', 0), reverse=True)
        regular.sort(key=lambda x: x.get('used', 0), reverse=True)

        num_entries = int(extension.preferences.get('num_entries', 10))

        for item in favourites:
            content = item.get("contents", "").strip()
            items.append(ExtensionResultItem(
                name=f"<b>{content}</b>",
                description="Favorite - Press Enter to copy",
                on_enter=CopyToClipboardAction(content),
                alt_action=ExtensionCustomAction(item, keep_app_open=True)
            ))

        for item in regular:
            content = item.get("contents", "").strip()
            items.append(ExtensionResultItem(
                name=content,
                description="Press Enter to copy",
                on_enter=CopyToClipboardAction(content),
                alt_action=ExtensionCustomAction(item, keep_app_open=True)
            ))

        return RenderResultListAction(items[:num_entries])

class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        item = event.get_data()
        home_dir = os.path.expanduser("~")
        registry_path = os.path.join(home_dir, ".cache", "clipboard-indicator@tudmotu.com", "registry.txt")

        try:
            with open(registry_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                for i, reg_item in enumerate(data):
                    if reg_item.get("contents") == item.get("contents"):
                        data[i]["favorite"] = not data[i].get("favorite", False)
                        break
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Handle error silently or log it

        # Refresh the list
        keyword = extension.preferences.get('clipboard_history')
        return SetUserQueryAction(f"{keyword} {event.get_query()}")


if __name__ == '__main__':
    ClipboardHistoryExtension().run()