import json
import os
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, path: str = "./data/reminders.json"):
        self.path = path
        self.data = self._load()

    def _load(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self._default_data()
        return self._default_data()

    def _default_data(self):
        return {
            "reminders": [],
            "activity": {},
            "notifications": [],
            "message_count": {}
        }

    def save(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)


    def add_reminder(self, name: str, message: str, time: str, is_recurring: bool, role_id: int = None):
        reminder = {
            "id": len(self.data["reminders"]) + 1,
            "name": name,
            "message": message,
            "time": time,
            "is_recurring": is_recurring,
            "role_id": role_id,
            "created_at": datetime.now().isoformat(),
            "enabled": True
        }
        self.data["reminders"].append(reminder)
        self.save()
        return reminder

    def get_reminders(self):
        return self.data["reminders"]

    def get_reminder(self, reminder_id: int):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                return reminder
        return None

    def delete_reminder(self, reminder_id: int):
        self.data["reminders"] = [r for r in self.data["reminders"] if r["id"] != reminder_id]
        self.save()

    def toggle_reminder(self, reminder_id: int):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                reminder["enabled"] = not reminder["enabled"]
                self.save()
                return reminder
        return None

    def update_reminder_time(self, reminder_id: int, time: str):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                reminder["time"] = time
                self.save()
                return reminder
        return None

    def update_reminder_name(self, reminder_id: int, name: str):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                reminder["name"] = name
                self.save()
                return reminder
        return None

    def update_reminder_message(self, reminder_id: int, message: str):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                reminder["message"] = message
                self.save()
                return reminder
        return None

    def update_reminder_roles(self, reminder_id: int, role_ids: list):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                reminder["role_ids"] = role_ids
                reminder["role_id"] = role_ids[0] if role_ids else None
                self.save()
                return reminder
        return None

    def add_reminder_roles(self, reminder_id: int, new_role_ids: list):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                current_roles = reminder.get("role_ids", [])
                if not current_roles and reminder.get("role_id"):
                    current_roles = [reminder["role_id"]]
                
                for rid in new_role_ids:
                    if rid not in current_roles:
                        current_roles.append(rid)
                
                reminder["role_ids"] = current_roles
                reminder["role_id"] = current_roles[0] if current_roles else None
                self.save()
                return reminder
        return None

    def remove_reminder_roles(self, reminder_id: int, remove_role_ids: list):
        for reminder in self.data["reminders"]:
            if reminder["id"] == reminder_id:
                current_roles = reminder.get("role_ids", [])
                if not current_roles and reminder.get("role_id"):
                    current_roles = [reminder["role_id"]]
                
                current_roles = [rid for rid in current_roles if rid not in remove_role_ids]
                
                reminder["role_ids"] = current_roles
                reminder["role_id"] = current_roles[0] if current_roles else None
                self.save()
                return reminder
        return None

    def add_activity(self, user_id: int, action: str):
        user_id = str(user_id)
        if user_id not in self.data["activity"]:
            self.data["activity"][user_id] = []
        
        self.data["activity"][user_id].append({
            "action": action,
            "timestamp": datetime.now().isoformat()
        })
        self.save()

    def get_user_activity(self, user_id: int, limit: int = 10):
        user_id = str(user_id)
        if user_id in self.data["activity"]:
            return self.data["activity"][user_id][-limit:]
        return []

    def get_top_active_users(self, limit: int = 10):
        activity_count = {
            int(user_id): len(actions) 
            for user_id, actions in self.data["activity"].items()
        }
        return sorted(activity_count.items(), key=lambda x: x[1], reverse=True)[:limit]


    def add_message(self, user_id: int):
        if "message_count" not in self.data:
            self.data["message_count"] = {}
        
        user_id = str(user_id)
        if user_id not in self.data["message_count"]:
            self.data["message_count"][user_id] = {
                "total": 0,
                "messages": []
            }
        
        self.data["message_count"][user_id]["total"] += 1
        self.data["message_count"][user_id]["messages"].append({
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.data["message_count"][user_id]["messages"]) > 10000:
            self.data["message_count"][user_id]["messages"] = \
                self.data["message_count"][user_id]["messages"][-10000:]
        
        self.save()

    def get_user_message_count(self, user_id: int, days: int = None):
        from datetime import timedelta
        
        user_id = str(user_id)
        if user_id not in self.data["message_count"]:
            return 0
        
        if days is None:
            return self.data["message_count"][user_id]["total"]
        
        cutoff_date = datetime.now() - timedelta(days=days)
        count = 0
        for msg in self.data["message_count"][user_id]["messages"]:
            msg_date = datetime.fromisoformat(msg["timestamp"])
            if msg_date > cutoff_date:
                count += 1
        
        return count

    def get_top_active_users_by_messages(self, limit: int = 100, days: int = None):
        from datetime import timedelta
        
        activity_count = {}
        
        if "message_count" not in self.data:
            return []
        
        for user_id, data in self.data["message_count"].items():
            if days is None:
                count = data.get("total", 0)
            else:
                cutoff_date = datetime.now() - timedelta(days=days)
                count = 0
                for msg in data.get("messages", []):
                    msg_date = datetime.fromisoformat(msg["timestamp"])
                    if msg_date > cutoff_date:
                        count += 1
            
            if count > 0:
                activity_count[int(user_id)] = count
        
        return sorted(activity_count.items(), key=lambda x: x[1], reverse=True)[:limit]


    def add_notification(self, title: str, message: str, role_ids: list):
        notification = {
            "id": len(self.data["notifications"]) + 1,
            "title": title,
            "message": message,
            "role_ids": role_ids,
            "created_at": datetime.now().isoformat()
        }
        self.data["notifications"].append(notification)
        self.save()
        return notification

    def get_notifications(self):
        return self.data["notifications"]
