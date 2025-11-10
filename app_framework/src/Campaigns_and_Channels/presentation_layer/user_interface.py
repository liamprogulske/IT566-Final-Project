"""Implements the applicatin user interface."""

from application_name.application_base import ApplicationBase
from application_name.service_layer.app_services import AppServices
import inspect
import json

from application_name.business_layer import campaign_service as svc

class UserInterface:
    def __init__(self, config):
        self.config = config
        self.running = True

    def start(self):
        print("=== Campaigns & Channels Console ===")
        print(f"Config loaded for DB: {self.config['database']['connection']['config']['database']}")
        while self.running:
            self.show_menu()

    def show_menu(self):
        print("\n1) List Campaigns\n2) List Channels\n3) Exit")
        choice = input("Select option: ").strip()
        if choice == "1":
            for c in svc.list_campaigns():
                print(f"[{c.campaign_id}] {c.name} | {c.status}")
        elif choice == "2":
            for ch in svc.list_channels():
                print(f"[{ch.channel_id}] {ch.name} ({ch.type})")
        elif choice == "3":
            self.running = False
            print("Goodbye!")
        else:
            print("Invalid choice.")
