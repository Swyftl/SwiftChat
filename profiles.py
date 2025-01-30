import json
import os

class ProfileManager:
    def __init__(self):
        self.profiles_file = 'profiles.json'
        self.profiles = self.load_profiles()

    def load_profiles(self):
        """Load profiles from file"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_profiles(self):
        """Save profiles to file"""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=4)

    def add_profile(self, name, username, password, host, port):
        """Add or update a profile"""
        self.profiles[name] = {
            'username': username,
            'password': password,
            'host': host,
            'port': port
        }
        self.save_profiles()

    def get_profile(self, name):
        """Get a profile by name"""
        return self.profiles.get(name)

    def delete_profile(self, name):
        """Delete a profile"""
        if name in self.profiles:
            del self.profiles[name]
            self.save_profiles()
            return True
        return False

    def get_profile_names(self):
        """Get list of profile names"""
        return list(self.profiles.keys())
