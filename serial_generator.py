"""
Aventa HFT Pro 2026 - Serial Key Generator with License Expiry System
Modern UI with compact layout, hardware binding, and expiry support
INCLUDING FOLDER PATH for enhanced security
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import uuid
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import hashlib
import os
import json
import subprocess
import socket

# ============================================================================
# HARDWARE ID GENERATOR WITH FOLDER PATH
# ============================================================================

class HardwareIDGenerator:
    """Generate unique hardware IDs from system information INCLUDING folder path"""
    
    @staticmethod
    def get_installation_folder():
        """Get the application installation folder"""
        try:
            # Get the folder where the program is running from
            app_folder = os.path.dirname(os.path.abspath(__file__))
            # Normalize the path to be consistent
            app_folder = os.path.normpath(app_folder).upper()
            return app_folder
        except:
            return "UNKNOWN_FOLDER"
    
    @staticmethod
    def generate():
        """Generate hardware ID from system UUID INCLUDING folder path"""
        try:
            # Combine system UUID with folder path for stronger binding
            hw_base = str(uuid.uuid1())
            installation_folder = HardwareIDGenerator.get_installation_folder()
            
            # Create combined string
            combined = f"{hw_base}|{installation_folder}"
            
            # Hash untuk consistency
            hw_id = hashlib.sha256(combined.encode()).hexdigest()[:32].upper()
            return hw_id
        except:
            return str(uuid.uuid4()).upper()
    
    @staticmethod
    def hash_hardware_id(hw_id):
        """Hash hardware ID for serial inclusion"""
        return hashlib.md5(hw_id.encode()).hexdigest()[:4].upper()


# ============================================================================
# SERIAL KEY GENERATOR WITH EXPIRY SUPPORT
# ============================================================================

class SerialKeyGenerator:
    """Generate encrypted serial keys with hardware binding and expiry"""
    
    SERIAL_PREFIX = "AV"
    SECRET_KEY = b'TluxwB3fV_js6ZY5_TluxwB3fV_js6ZY5Tlu-RS='  # Base key
    
    @staticmethod
    def generate_serial(hardware_id, expiry_days=-1):
        """
        Generate serial key for given hardware ID
        Args:
            hardware_id: Hardware ID string
            expiry_days: -1 for unlimited, 7 for trial, N for custom days
        Returns:
            Serial key string
        """
        # Hash hardware ID for checksum
        hw_hash = HardwareIDGenerator.hash_hardware_id(hardware_id)
        
        # Generate random components
        import random
        import string
        
        seg1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        seg2 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        seg3 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        # Create serial format: AV-XXXX-XXXX-XXXX-HHHH
        serial = f"{SerialKeyGenerator.SERIAL_PREFIX}-{seg1}-{seg2}-{seg3}-{hw_hash}"
        
        # Create data to encrypt
        expiry_date = None
        if expiry_days != -1:
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
        
        data = {
            "serial": serial,
            "hardware_id": hardware_id,
            "created": datetime.now().isoformat(),
            "expiry_date": expiry_date,
            "expiry_days": expiry_days
        }
        
        return serial, data
    
    @staticmethod
    def encrypt_data(data):
        """Encrypt license data"""
        try:
            cipher = Fernet(SerialKeyGenerator.SECRET_KEY)
            json_str = json.dumps(data)
            encrypted = cipher.encrypt(json_str.encode())
            return encrypted.decode()
        except:
            return None
    
    @staticmethod
    def decrypt_data(encrypted_str):
        """Decrypt license data"""
        try:
            cipher = Fernet(SerialKeyGenerator.SECRET_KEY)
            decrypted = cipher.decrypt(encrypted_str.encode())
            return json.loads(decrypted.decode())
        except:
            return None


# ============================================================================
# MODERN UI STYLE
# ============================================================================

class ModernStyle:
    """Modern color scheme and styling constants"""
    
    # Color Palette
    PRIMARY = "#2E86AB"      # Professional Blue
    SECONDARY = "#A23B72"   # Purple
    SUCCESS = "#06A77D"     # Green
    ACCENT = "#F18F01"      # Orange
    DANGER = "#D62828"      # Red
    
    # Background Colors
    BG_LIGHT = "#F5F7FA"
    BG_CARD = "#FFFFFF"
    
    # Text Colors
    TEXT_LIGHT = "#FFFFFF"
    TEXT_PRIMARY = "#1A1A1A"
    TEXT_SECONDARY = "#666666"
    
    # Borders
    BORDER = "#E0E0E0"
    
    @staticmethod
    def setup_styles(root):
        """Setup TTK styles"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=ModernStyle.BG_LIGHT)
        style.configure('TLabel', background=ModernStyle.BG_LIGHT, foreground=ModernStyle.TEXT_PRIMARY)


# ============================================================================
# MAIN GUI APPLICATION
# ============================================================================

class SerialGeneratorGUI:
    """Modern Serial Generator GUI with compact layout"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Aventa HFT Pro 2026 - Serial Generator v7.3.6")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # Configure style
        ModernStyle.setup_styles(root)
        root.configure(bg=ModernStyle.BG_LIGHT)
        
        # Initialize
        self.setup_ui()
        self.log_message("✅ Serial Generator Ready")
    
    def setup_ui(self):
        """Setup user interface with compact layout"""
        
        # Main container with scrollbar
        main_container = tk.Frame(self.root, bg=ModernStyle.BG_LIGHT)
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Canvas and scrollbar for scrollable content
        canvas = tk.Canvas(
            main_container,
            bg=ModernStyle.BG_LIGHT,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=ModernStyle.BG_LIGHT)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        main_frame = scrollable_frame
        
        # ===== HEADER SECTION =====
        header_frame = tk.Frame(main_frame, bg=ModernStyle.PRIMARY, height=50)
        header_frame.pack(fill=tk.X, pady=(0, 10), ipady=8, expand=False)
        
        title_label = tk.Label(
            header_frame,
            text="🔐 Serial Number Generator",
            font=("Segoe UI", 14, "bold"),
            bg=ModernStyle.PRIMARY,
            fg=ModernStyle.TEXT_LIGHT
        )
        title_label.pack(pady=4)
        
        # ===== INPUT SECTION =====
        input_frame = tk.Frame(main_frame, bg=ModernStyle.BG_CARD, relief=tk.FLAT, bd=1)
        input_frame.pack(fill=tk.X, pady=8)
        input_frame.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        input_title = tk.Label(
            input_frame,
            text="Hardware Information",
            font=("Segoe UI", 10, "bold"),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.PRIMARY
        )
        input_title.pack(anchor=tk.W, padx=10, pady=(8, 5))
        
        # ===== FOLDER PATH INFO =====
        folder_info_frame = tk.Frame(
            input_frame,
            bg="#2a2a2a",
            relief=tk.FLAT,
            bd=1
        )
        folder_info_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
        folder_info_frame.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        folder_label = tk.Label(
            folder_info_frame,
            text="📁 Installation Folder (termasuk dalam Hardware ID):",
            font=("Segoe UI", 8, "bold"),
            bg="#2a2a2a",
            fg="#FFD700"
        )
        folder_label.pack(anchor=tk.W, padx=8, pady=(4, 2))
        
        installation_folder = HardwareIDGenerator.get_installation_folder()
        folder_display = tk.Label(
            folder_info_frame,
            text=installation_folder,
            font=("Courier", 8),
            bg="#2a2a2a",
            fg="#87CEEB",
            wraplength=400,
            justify=tk.LEFT
        )
        folder_display.pack(anchor=tk.W, padx=8, pady=(0, 4))
        
        folder_warning = tk.Label(
            folder_info_frame,
            text="⚠️ Jika program dipindahkan ke folder berbeda, serial number harus diaktifkan ulang!",
            font=("Segoe UI", 8),
            bg="#2a2a2a",
            fg="#FF6B6B"
        )
        folder_warning.pack(anchor=tk.W, padx=8, pady=(0, 4))
        
        # Input label and field
        input_label = tk.Label(
            input_frame,
            text="Enter Hardware ID:",
            font=("Segoe UI", 9),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY
        )
        input_label.pack(anchor=tk.W, padx=10)
        
        self.hardware_id_entry = tk.Entry(
            input_frame,
            width=50,
            font=("Courier", 9),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=1
        )
        self.hardware_id_entry.pack(fill=tk.X, padx=10, pady=(3, 5))
        self.hardware_id_entry.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        hint_label = tk.Label(
            input_frame,
            text="(Customer should get this from their system)",
            font=("Segoe UI", 8),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_SECONDARY
        )
        hint_label.pack(anchor=tk.W, padx=10, pady=(0, 8))
        
        # ===== OR SECTION =====
        or_frame = tk.Frame(main_frame, bg=ModernStyle.BG_LIGHT)
        or_frame.pack(fill=tk.X, pady=6)
        
        ttk.Separator(or_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 2))
        or_label = tk.Label(or_frame, text="OR", font=("Segoe UI", 9), bg=ModernStyle.BG_LIGHT, fg=ModernStyle.TEXT_SECONDARY)
        or_label.pack()
        ttk.Separator(or_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(2, 0))
        
        # ===== AUTO-GENERATE SECTION =====
        auto_frame = tk.Frame(main_frame, bg=ModernStyle.BG_CARD, relief=tk.FLAT, bd=1)
        auto_frame.pack(fill=tk.X, pady=8)
        auto_frame.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        auto_title = tk.Label(
            auto_frame,
            text="Auto-Generate (for Testing)",
            font=("Segoe UI", 10, "bold"),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.PRIMARY
        )
        auto_title.pack(anchor=tk.W, padx=10, pady=(8, 6))
        
        auto_button = tk.Button(
            auto_frame,
            text="🎲 Generate Test Hardware ID",
            command=self.generate_test_hardware_id,
            bg=ModernStyle.PRIMARY,
            fg=ModernStyle.TEXT_LIGHT,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=6,
            cursor="hand2"
        )
        auto_button.pack(padx=10, pady=(0, 8))
        
        # ===== OUTPUT SECTION =====
        output_frame = tk.Frame(main_frame, bg=ModernStyle.BG_CARD, relief=tk.FLAT, bd=1)
        output_frame.pack(fill=tk.X, pady=8)
        output_frame.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        output_title = tk.Label(
            output_frame,
            text="Generated Serial Number",
            font=("Segoe UI", 10, "bold"),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.PRIMARY
        )
        output_title.pack(anchor=tk.W, padx=10, pady=(8, 6))
        
        self.serial_display = tk.Text(
            output_frame,
            height=3,
            width=50,
            font=("Courier", 10, "bold"),
            fg=ModernStyle.SUCCESS,
            bg="#F0F8F4",
            relief=tk.FLAT,
            bd=0
        )
        self.serial_display.pack(fill=tk.X, padx=10, pady=6)
        
        # ===== LICENSE TYPE SECTION =====
        license_frame = tk.Frame(main_frame, bg=ModernStyle.BG_CARD, relief=tk.FLAT, bd=1)
        license_frame.pack(fill=tk.X, pady=8)
        license_frame.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        license_title = tk.Label(
            license_frame,
            text="License Type",
            font=("Segoe UI", 10, "bold"),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.PRIMARY
        )
        license_title.pack(anchor=tk.W, padx=10, pady=(8, 5))
        
        self.license_type_var = tk.StringVar(value="unlimited")
        
        # Radio buttons
        radio_frame = tk.Frame(license_frame, bg=ModernStyle.BG_CARD)
        radio_frame.pack(anchor=tk.W, padx=10, pady=3)
        
        radio1 = tk.Radiobutton(
            radio_frame,
            text="🔓 Unlimited (No expiry)",
            variable=self.license_type_var,
            value="unlimited",
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            selectcolor=ModernStyle.BG_CARD
        )
        radio1.pack(anchor=tk.W, pady=2)
        
        radio2 = tk.Radiobutton(
            radio_frame,
            text="⏱️ Trial 7 Days (auto expire)",
            variable=self.license_type_var,
            value="trial",
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            selectcolor=ModernStyle.BG_CARD
        )
        radio2.pack(anchor=tk.W, pady=2)
        
        radio3 = tk.Radiobutton(
            radio_frame,
            text="📅 Custom Days",
            variable=self.license_type_var,
            value="custom",
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            font=("Segoe UI", 9),
            cursor="hand2",
            selectcolor=ModernStyle.BG_CARD
        )
        radio3.pack(anchor=tk.W, pady=2)
        
        # Custom days input
        custom_days_frame = tk.Frame(license_frame, bg=ModernStyle.BG_CARD)
        custom_days_frame.pack(anchor=tk.W, padx=30, pady=(3, 8))
        
        custom_label = tk.Label(
            custom_days_frame,
            text="Number of days:",
            font=("Segoe UI", 9),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY
        )
        custom_label.pack(side=tk.LEFT, padx=(0, 8))
        
        self.custom_days_entry = tk.Entry(
            custom_days_frame,
            width=8,
            font=("Segoe UI", 9),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=1
        )
        self.custom_days_entry.pack(side=tk.LEFT)
        self.custom_days_entry.insert(0, "30")
        self.custom_days_entry.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        # ===== BUTTON SECTION =====
        button_frame = tk.Frame(main_frame, bg=ModernStyle.BG_LIGHT)
        button_frame.pack(fill=tk.X, pady=8)
        
        generate_btn = tk.Button(
            button_frame,
            text="✨ Generate Serial",
            command=self.generate_serial,
            bg=ModernStyle.SUCCESS,
            fg=ModernStyle.TEXT_LIGHT,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        copy_btn = tk.Button(
            button_frame,
            text="📋 Copy Serial",
            command=self.copy_serial,
            bg=ModernStyle.PRIMARY,
            fg=ModernStyle.TEXT_LIGHT,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        copy_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            button_frame,
            text="🔄 Clear",
            command=self.clear_all,
            bg=ModernStyle.ACCENT,
            fg=ModernStyle.TEXT_LIGHT,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # ===== LOG SECTION =====
        log_title = tk.Label(
            main_frame,
            text="Generation Log",
            font=("Segoe UI", 10, "bold"),
            bg=ModernStyle.BG_LIGHT,
            fg=ModernStyle.PRIMARY
        )
        log_title.pack(anchor=tk.W, pady=(8, 6))
        
        log_frame = tk.Frame(main_frame, bg=ModernStyle.BG_CARD, relief=tk.FLAT, bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        log_frame.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
        
        self.log_text = tk.Text(
            log_frame,
            height=6,
            width=60,
            font=("Courier", 8),
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            bd=0,
            padx=8,
            pady=6
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log_text.configure(highlightbackground=ModernStyle.BORDER, highlightthickness=1)
    
    def generate_test_hardware_id(self):
        """Generate test hardware ID"""
        hw_id = HardwareIDGenerator.generate()
        self.hardware_id_entry.delete(0, tk.END)
        self.hardware_id_entry.insert(0, hw_id)
        
        installation_folder = HardwareIDGenerator.get_installation_folder()
        self.log_message(f"🎲 Generated test HW ID: {hw_id}")
        self.log_message(f"📁 Installation Folder: {installation_folder}")
        self.log_message(f"⚠️  Serial number ini terikat ke folder spesifik ini!")
        self.log_message(f"    Jika folder berubah → serial tidak berlaku → perlu aktivasi ulang")
    
    def generate_serial(self):
        """Generate serial key based on input"""
        hw_id = self.hardware_id_entry.get().strip()
        
        if not hw_id:
            messagebox.showerror("Error", "Please enter or generate a Hardware ID")
            self.log_message("❌ Error: Hardware ID is empty")
            return
        
        # Get license type
        license_type = self.license_type_var.get()
        expiry_days = -1
        
        if license_type == "trial":
            expiry_days = 7
        elif license_type == "custom":
            try:
                expiry_days = int(self.custom_days_entry.get())
                if expiry_days < 1:
                    raise ValueError
            except:
                messagebox.showerror("Error", "Invalid number of days")
                self.log_message("❌ Error: Invalid custom days value")
                return
        
        # Generate serial
        serial, data = SerialKeyGenerator.generate_serial(hw_id, expiry_days)
        
        # Display serial
        self.serial_display.delete("1.0", tk.END)
        self.serial_display.insert(tk.END, serial)
        
        # Log message with folder information
        expiry_info = ""
        if expiry_days == -1:
            expiry_info = " (Unlimited)"
        elif expiry_days == 7:
            expiry_info = " (Trial 7 Days)"
        else:
            expiry_info = f" (Custom: {expiry_days} Days)"
        
        installation_folder = HardwareIDGenerator.get_installation_folder()
        
        self.log_message(f"✅ Serial Generated{expiry_info}")
        self.log_message(f"📁 Bound to folder: {installation_folder}")
        self.log_message(f"⚠️  PENTING: Serial ini berlaku HANYA untuk folder ini!")
        self.log_message(f"    Jika program dipindahkan ke folder lain, serial tidak akan berfungsi")
        self.log_message(f"   Hardware ID: {hw_id}")
        self.log_message(f"   Serial: {serial}")
    
    def copy_serial(self):
        """Copy serial to clipboard"""
        serial = self.serial_display.get("1.0", tk.END).strip()
        
        if not serial:
            messagebox.showwarning("Warning", "No serial to copy")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(serial)
        self.log_message("📋 Serial copied to clipboard")
        messagebox.showinfo("Success", "Serial copied to clipboard!")
    
    def clear_all(self):
        """Clear all fields"""
        self.hardware_id_entry.delete(0, tk.END)
        self.serial_display.delete("1.0", tk.END)
        self.custom_days_entry.delete(0, tk.END)
        self.custom_days_entry.insert(0, "30")
        self.log_message("🔄 All fields cleared")
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        # Keep only last 100 lines
        lines = int(self.log_text.index(tk.END).split('.')[0])
        if lines > 100:
            self.log_text.delete("1.0", "2.0")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialGeneratorGUI(root)
    root.mainloop()
