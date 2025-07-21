from typing import Callable, Dict, List, Any

class EventType:
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    ERROR = "error"
    DATA_UPDATED = "data_updated"
    # Добавьте другие события по необходимости

class EventSystem:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Any], None]):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]):
        if event_type in self._listeners:
            self._listeners[event_type] = [cb for cb in self._listeners[event_type] if cb != callback]

    def emit_event(self, event_type: str, data: Any = None):
        print(f"[EVENT] {event_type}: {data}")
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[EVENT ERROR] {event_type}: {e}")

    # Для обратной совместимости с плагинами
    def emit(self, *args, **kwargs):
        # Поддержка вызовов с разным числом аргументов
        if len(args) == 0:
            return
        event_type = args[0]
        data = args[1] if len(args) > 1 else None
        # Остальные параметры игнорируем, но можно логировать
        print(f"[EVENT emit] type={event_type}, data={data}, extra_args={args[2:]}, kwargs={kwargs}")
        self.emit_event(event_type, data)

# Глобальный экземпляр для импортов
event_system = EventSystem() 