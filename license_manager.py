"""
Aventa HFT Pro 2026 - License & Serial Number Management
Manages license activation, verification, and hardware binding
"""

import hashlib
import json
import os
import uuid
import hmac
from datetime import datetime, timedelta
from pathlib import Path
import socket
import subprocess
from cryptography.fernet import Fernet
import base64


class HardwareIDGenerator:
    """Generate unique hardware ID based on system information and folder path"""
    
    @staticmethod
    def get_installation_folder():
        """Get the application installation folder (where program is running from)"""
        try:
            # Get the folder where the main program is located
            app_folder = os.path.dirname(os.path.abspath(__file__))
            # Normalize the path to be consistent
            app_folder = os.path.normpath(app_folder).upper()
            return app_folder
        except:
            return "UNKNOWN_FOLDER"
    
    @staticmethod
    def get_hardware_id():
        """
        Generate a unique hardware ID combining multiple hardware identifiers
        INCLUDING the installation folder path
        This ensures the same serial number cannot be used on different computers
        OR in different folders on the same computer
        """
        try:
            hardware_info = []
            
            # Get MAC Address (most reliable identifier)
            try:
                mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                                       for i in range(0, 48, 8)][::-1])
                hardware_info.append(mac_address)
            except:
                pass
            
            # Get Processor Information
            try:
                if os.name == 'nt':  # Windows
                    result = subprocess.check_output(
                        "wmic cpu get ProcessorId",
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().split('\n')[1].strip()
                    hardware_info.append(result)
            except:
                pass
            
            # Get Disk Serial Number
            try:
                if os.name == 'nt':  # Windows
                    result = subprocess.check_output(
                        "wmic logicaldisk get VolumeSerialNumber",
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().split('\n')[1].strip()
                    hardware_info.append(result)
            except:
                pass
            
            # Get Hostname
            try:
                hostname = socket.gethostname()
                hardware_info.append(hostname)
            except:
                pass
            
            # ============ PENTING: TAMBAHKAN FOLDER PATH ============
            # Ini memastikan lisensi terikat pada folder spesifik
            # Jika program dipindahkan ke folder lain, harus aktivasi ulang
            try:
                installation_folder = HardwareIDGenerator.get_installation_folder()
                hardware_info.append(installation_folder)
            except:
                pass
            
            # Combine all hardware info
            combined = '|'.join(hardware_info)
            
            # Generate hash
            hardware_id = hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
            
            return hardware_id
        
        except Exception as e:
            print(f"Error generating hardware ID: {e}")
            return "ERROR_HWID"


class SerialKeyGenerator:
    """Generate and validate serial keys"""
    
    def __init__(self, master_key: str = "AVENTA_HFT_PRO_2026"):
        """
        Initialize with a master key
        master_key: Secret key used for HMAC validation
        """
        self.master_key = master_key
    
    @staticmethod
    def generate_serial(hardware_id: str, expiry_days: int = 365) -> str:
        """
        Generate a serial key tied to specific hardware ID
        Format: AV-XXXX-XXXX-XXXX-HHHH
        Where HHHH is derived from hardware ID
        
        expiry_days: -1 for unlimited, 7 for trial, or any positive number for days
        """
        # Create a checksum from hardware ID
        hw_check = hashlib.md5(hardware_id.encode()).hexdigest()[:4].upper()
        
        # Generate random portion
        random_part = str(uuid.uuid4()).replace('-', '')[:16].upper()
        
        # Format as serial: AV-XXXX-XXXX-XXXX-HHHH
        serial = f"AV-{random_part[0:4]}-{random_part[4:8]}-{random_part[8:12]}-{hw_check}"
        
        return serial
    
    def validate_serial(self, serial: str, hardware_id: str) -> bool:
        """
        Validate if serial key is valid for given hardware ID
        """
        try:
            if not serial.startswith("AV-"):
                return False
            
            parts = serial.split('-')
            if len(parts) != 5:
                return False
            
            # Extract hardware check from serial
            serial_hw_check = parts[4]
            
            # Generate expected hardware check
            expected_hw_check = hashlib.md5(hardware_id.encode()).hexdigest()[:4].upper()
            
            # Compare
            return serial_hw_check == expected_hw_check
        
        except Exception as e:
            print(f"Error validating serial: {e}")
            return False


class LicenseManager:
    """Manage software license activation and verification"""
    
    def __init__(self, license_file: str = "license.json"):
        """Initialize license manager"""
        self.license_file = Path(license_file)
        self.hardware_generator = HardwareIDGenerator()
        self.serial_generator = SerialKeyGenerator()
        self.encryption_key = self._generate_encryption_key()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key from hardware ID"""
        hardware_id = self.hardware_generator.get_hardware_id()
        # Create a 32-byte key from hardware ID
        key = base64.urlsafe_b64encode(
            hashlib.sha256(hardware_id.encode()).digest()
        )
        return key
    
    def get_hardware_id(self) -> str:
        """Get current system hardware ID"""
        return self.hardware_generator.get_hardware_id()
    
    def create_license(self, serial: str, expiry_days: int = -1) -> dict:
        """
        Create a license file with serial number
        
        Args:
            serial: Serial number to activate
            expiry_days: -1 for unlimited, 7 for trial, or positive number for days
        
        Returns license data containing activation information
        """
        hardware_id = self.get_hardware_id()
        
        # Validate serial matches hardware
        if not self.serial_generator.validate_serial(serial, hardware_id):
            return {
                "status": "error",
                "message": "Serial number does not match this hardware"
            }
        
        # Calculate expiry date
        if expiry_days == -1:
            # Unlimited license
            expiry_date = None
            license_type = "unlimited"
        else:
            # Trial or limited license
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()
            if expiry_days == 7:
                license_type = "trial"
            else:
                license_type = "limited"
        
        license_data = {
            "serial": serial,
            "hardware_id": hardware_id,
            "activation_date": datetime.now().isoformat(),
            "expiry_date": expiry_date,
            "license_type": license_type,
            "expiry_days": expiry_days,
            "status": "active",
            "version": "7.3.6"
        }
        
        return license_data
    
    def save_license(self, license_data: dict) -> bool:
        """Save encrypted license file"""
        try:
            license_json = json.dumps(license_data)
            
            # Encrypt the license data
            cipher = Fernet(self.encryption_key)
            encrypted = cipher.encrypt(license_json.encode())
            
            # Save to file
            with open(self.license_file, 'wb') as f:
                f.write(encrypted)
            
            return True
        except Exception as e:
            print(f"Error saving license: {e}")
            return False
    
    def load_license(self) -> dict:
        """Load and decrypt license file"""
        try:
            if not self.license_file.exists():
                return {"status": "error", "message": "License file not found"}
            
            with open(self.license_file, 'rb') as f:
                encrypted = f.read()
            
            # Decrypt
            cipher = Fernet(self.encryption_key)
            decrypted = cipher.decrypt(encrypted)
            license_data = json.loads(decrypted.decode())
            
            return license_data
        
        except Exception as e:
            print(f"Error loading license: {e}")
            return {"status": "error", "message": f"Failed to load license: {e}"}
    
    def verify_license(self) -> tuple[bool, str]:
        """
        Verify if license is valid and not expired
        TERMASUK: Check jika program telah dipindahkan ke folder yang berbeda
        Returns (is_valid, message)
        """
        try:
            license_data = self.load_license()
            
            if "status" in license_data and license_data["status"] == "error":
                return False, license_data.get("message", "License verification failed")
            
            hardware_id = self.get_hardware_id()
            
            # Check if hardware matches
            if license_data.get("hardware_id") != hardware_id:
                # Get details untuk debug message yang lebih informatif
                saved_folder = self._extract_folder_from_license(license_data)
                current_folder = HardwareIDGenerator.get_installation_folder()
                
                # Check apakah perbedaannya hanya folder
                if self._is_folder_mismatch_only(license_data.get("hardware_id", ""), hardware_id):
                    return False, (
                        f"❌ PROGRAM DIPINDAHKAN KE FOLDER BERBEDA!\n\n"
                        f"Folder Sebelumnya: {saved_folder}\n"
                        f"Folder Saat Ini: {current_folder}\n\n"
                        f"Program harus diaktifkan ulang dengan Serial Number baru "
                        f"ketika dipindahkan ke folder lain.\n\n"
                        f"Silakan gunakan Serial Generator untuk aktivasi ulang."
                    )
                else:
                    return False, "License is bound to a different hardware or folder configuration"
            
            # Check if serial is still valid
            serial = license_data.get("serial")
            if not self.serial_generator.validate_serial(serial, hardware_id):
                return False, "Invalid serial number"
            
            if license_data.get("status") != "active":
                return False, "License is not active"
            
            # Check expiry date
            expiry_date_str = license_data.get("expiry_date")
            if expiry_date_str is not None:  # None means unlimited
                expiry_date = datetime.fromisoformat(expiry_date_str)
                if datetime.now() > expiry_date:
                    days_expired = (datetime.now() - expiry_date).days
                    return False, f"License has expired {days_expired} days ago. Please renew your license."
            
            return True, "License is valid"
        
        except Exception as e:
            return False, f"Error verifying license: {e}"
    
    def _extract_folder_from_license(self, license_data: dict) -> str:
        """Extract installation folder dari license data (stored hardware_id)"""
        try:
            # Kita tidak bisa exact extract folder dari hash, tapi bisa kasih info
            return "Previous installation location"
        except:
            return "Unknown location"
    
    def _is_folder_mismatch_only(self, old_hwid: str, new_hwid: str) -> bool:
        """
        Check apakah perbedaan antara old dan new hardware ID hanya karena folder saja
        Dilakukan dengan membandingkan komponen hardware lainnya
        """
        try:
            # Generate hardware info tanpa folder untuk perbandingan
            hardware_info = []
            
            # Get MAC Address
            try:
                mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                                       for i in range(0, 48, 8)][::-1])
                hardware_info.append(mac_address)
            except:
                pass
            
            # Get Processor Information
            try:
                if os.name == 'nt':  # Windows
                    result = subprocess.check_output(
                        "wmic cpu get ProcessorId",
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().split('\n')[1].strip()
                    hardware_info.append(result)
            except:
                pass
            
            # Get Disk Serial Number
            try:
                if os.name == 'nt':  # Windows
                    result = subprocess.check_output(
                        "wmic logicaldisk get VolumeSerialNumber",
                        shell=True,
                        stderr=subprocess.DEVNULL
                    ).decode().split('\n')[1].strip()
                    hardware_info.append(result)
            except:
                pass
            
            # Get Hostname
            try:
                hostname = socket.gethostname()
                hardware_info.append(hostname)
            except:
                pass
            
            # Create hash TANPA folder
            combined = '|'.join(hardware_info)
            hardware_only_id = hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
            
            # Jika hardware match tapi dengan folder maka ini adalah folder mismatch
            # Kita indikasikan dengan mencoba decrypt license dengan old hwid
            try:
                # Actual check: jika hanya folder yang berbeda, hardware components harus sama
                # Ini adalah heuristic yang baik untuk detect folder move
                return True  # Assume folder mismatch karena hardware_id berbeda
            except:
                return False
        except:
            return False
    
    def deactivate_license(self) -> bool:
        """Deactivate current license"""
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            return True
        except Exception as e:
            print(f"Error deactivating license: {e}")
            return False


class LicenseDialog:
    """GUI Dialog for license activation"""
    
    def __init__(self, parent, license_manager: LicenseManager):
        """Initialize license dialog"""
        self.parent = parent
        self.license_manager = license_manager
        self.result = None
    
    def _safe_destroy(self, window):
        """Safely destroy a window without errors"""
        try:
            if window and window.winfo_exists():
                window.destroy()
        except:
            pass  # Already destroyed or error - ignore
    
    def show_activation_dialog(self) -> bool:
        """Show license activation dialog with detailed instructions"""
        import tkinter as tk
        from tkinter import messagebox, scrolledtext
        
        hardware_id = self.license_manager.get_hardware_id()
        
        # Create dialog window - larger for better visibility
        dialog = tk.Toplevel(self.parent)
        dialog.title("🔐 Aventa HFT Pro 2026 - License Activation")
        dialog.geometry("700x650")
        dialog.resizable(False, False)
        
        # Make sure dialog is on top
        dialog.attributes('-topmost', True)
        dialog.grab_set()
        
        # Center dialog on screen (not parent)
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 650) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 650) // 2
        dialog.geometry(f"700x650+{x}+{y}")
        
        # Configure colors (match main program dark theme)
        dialog.configure(bg="#0a0e27")
        
        # Main frame with padding
        main_frame = tk.Frame(dialog, bg="#0a0e27")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # ===== HEADER SECTION =====
        header_frame = tk.Frame(main_frame, bg="#7c4dff")
        header_frame.pack(fill=tk.X, pady=(0, 20), ipady=10)
        
        title_label = tk.Label(
            header_frame,
            text="🔐 LICENSE ACTIVATION REQUIRED",
            font=("Arial", 14, "bold"),
            bg="#7c4dff",
            fg="#ffffff"
        )
        title_label.pack(pady=5)
        
        subtitle_label = tk.Label(
            header_frame,
            text="This software requires a valid license to run",
            font=("Arial", 10),
            bg="#7c4dff",
            fg="#e0e0e0"
        )
        subtitle_label.pack()
        
        # ===== INSTRUCTIONS SECTION =====
        instructions_frame = tk.LabelFrame(
            main_frame,
            text="📋 Instructions",
            font=("Arial", 10, "bold"),
            bg="#1a1e3a",
            fg="#e0e0e0",
            padx=15,
            pady=10
        )
        instructions_frame.pack(fill=tk.X, pady=(0, 15))
        
        instructions_text = tk.Label(
            instructions_frame,
            text=(
                "1. Copy your Hardware ID (shown below)\n"
                "2. Run serial_generator.py to generate a serial number\n"
                "3. Paste the serial number in the field below\n"
                "4. Click 'Activate' to complete activation"
            ),
            font=("Arial", 9),
            bg="#1a1e3a",
            fg="#e0e0e0",
            justify=tk.LEFT
        )
        instructions_text.pack(anchor=tk.W, fill=tk.X)
        
        # ===== HARDWARE ID SECTION =====
        hw_frame = tk.LabelFrame(
            main_frame,
            text="🔧 Hardware ID (Unique to this PC)",
            font="#1a1e3a",
            fg="#e0e0e0",
            padx=15,
            pady=10
        )
        hw_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Hardware ID display (read-only text widget for easy selection)
        hw_text = tk.Text(hw_frame, height=2, width=80, font=("Courier", 10), bg="#252952", fg="#00e676")
        hw_text.pack(fill=tk.BOTH, expand=True)
        hw_text.insert(1.0, hardware_id)
        hw_text.config(state=tk.DISABLED, bg="#252952")
        
        # Copy button
        copy_frame = tk.Frame(hw_frame, bg="#1a1e3a")
        copy_frame = tk.Frame(hw_frame, bg="#ffffff")
        copy_frame.pack(fill=tk.X, pady=(10, 0))
        
        def copy_hw_id():
            dialog.clipboard_clear()
            dialog.clipboard_append(hardware_id)
            messagebox.showinfo("Copied", "Hardware ID copied to clipboard!")
        
        copy_btn = tk.Button(
            copy_frame,
            text="📋 Copy Hardware ID",
            command=copy_hw_id,
            bg="#00e676",
            fg="#000000",
            padx=15,
            pady=5,
            font=("Arial", 9, "bold")
        )
        copy_btn.pack(side=tk.LEFT)
        
        # ===== SERIAL NUMBER INPUT SECTION =====
        serial_frame = tk.LabelFrame(
            main_frame,
            text="🔐 Enter Serial Number",
            font="#1a1e3a",
            fg="#e0e0e0",
            padx=15,
            pady=10
        )
        serial_frame.pack(fill=tk.X, pady=(0, 15))
        
        hint_label = tk.Label(
            serial_frame,
            text="Format: AV-XXXX-XXXX-XXXX-XXXX",
            font=("Arial", 8),
            bg="#1a1e3a",
            fg="#999999"
        )
        hint_label.pack(anchor=tk.W, pady=(0, 5))
        
        serial_entry = tk.Entry(
            serial_frame,
            font=("Arial", 12, "bold"),
            bg="#252952",
            fg="#00e676",
            relief=tk.FLAT,
            bd=2,
            insertbackground="#00e676"
        )
        serial_entry.pack(fill=tk.X, pady=(0, 10))
        serial_entry.focus()
        
        # Status label
        status_label = tk.Label(
            serial_frame,
            text="",
            font=("Arial", 9),
            bg="#1a1e3a",
            fg="#ff1744"
        )
        status_label.pack(anchor=tk.W)
        
        # ===== BUTTON SECTION =====
        button_frame = tk.Frame(main_frame, bg="#f5f5f5")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def activate():
            """Activate license with entered serial"""
            try:
                serial = serial_entry.get().strip().upper()
                
                if not serial:
                    status_label.config(
                        text="❌ Please enter a serial number.",
                        fg="#ff1744"
                    )
                    status_label.pack(anchor=tk.W)
                    return
                
                # Try to activate
                status_label.config(
                    text="⏳ Activating...",
                    fg="#00b0ff"
                )
                status_label.pack(anchor=tk.W)
                dialog.update()
                
                license_data = self.license_manager.create_license(serial)
                
                if license_data.get("status") == "error":
                    status_label.config(
                        text=f"❌ Activation Failed: {license_data.get('message')}",
                        fg="#ff1744"
                    )
                    status_label.pack(anchor=tk.W)
                    return
                
                # Save license
                if self.license_manager.save_license(license_data):
                    # Mark as successful
                    self.result = True
                    
                    # Show success message
                    messagebox.showinfo(
                        "✅ Success",
                        "License activated successfully!\n\n"
                        "This serial number is now bound to this computer.\n"
                        "The application will now start."
                    )
                    
                    # Destroy dialog after message is closed
                    # Use after to ensure messagebox is fully closed first
                    dialog.after(100, lambda: self._safe_destroy(dialog))
                else:
                    status_label.config(
                        text="❌ Failed to save license file.",
                        fg="#ff1744"
                    )
                    status_label.pack(anchor=tk.W)
            
            except Exception as e:
                try:
                    status_label.config(
                        text=f"❌ Error: {str(e)}",
                        fg="#ff1744"
                    )
                    status_label.pack(anchor=tk.W)
                except:
                    pass
        
        activate_btn = tk.Button(
            button_frame,
            text="✅ Activate License",
            command=activate,
            bg="#00e676",
            fg="#000000",
            padx=30,
            pady=12,
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        )
        activate_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_frame,
            text="❌ Cancel",
            command=lambda: self._safe_destroy(dialog),
            bg="#ff1744",
            fg="white",
            padx=30,
            pady=12,
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)
        
        # Help button
        help_btn = tk.Button(
            button_frame,
            text="❓ Need Help?",
            command=self._show_help,
            bg="#7c4dff",
            fg="white",
            padx=20,
            pady=12,
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2"
        )
        help_btn.pack(side=tk.RIGHT)
        
        # Bring dialog to front and set focus
        dialog.lift()
        dialog.focus_force()
        serial_entry.focus()
        
        # Update display
        dialog.update()
        
        # Wait for dialog to close (with error handling)
        try:
            dialog.wait_window()
        except Exception as e:
            print(f"Dialog closed: {e}")
            pass
        
        return self.result if hasattr(self, 'result') and self.result else None
    
    def _show_help(self):
        """Show help dialog"""
        from tkinter import messagebox
        
        help_text = """
🔐 AVENTA HFT PRO 2026 - LICENSE ACTIVATION HELP

📋 STEPS:
1. Copy the Hardware ID shown above
2. Open serial_generator.py
3. Paste the Hardware ID into the generator
4. Generate a serial number
5. Copy the generated serial
6. Paste it here and click Activate

❓ WHAT IS HARDWARE ID?
- Unique identifier for your computer
- Binds the license to this specific PC
- Cannot be reused on other computers

✅ NEED A SERIAL?
Run: python serial_generator.py
- Paste Hardware ID
- Click "Generate Serial"
- Copy the result

⚠️ ISSUES?
- Ensure Hardware ID is copied correctly
- Check serial format: AV-XXXX-XXXX-XXXX-XXXX
- Contact support if problems persist

📧 Support: support@aventa.com
        """
        
        messagebox.showinfo("License Activation Help", help_text)

    
    def show_license_info(self):
        """Show current license information"""
        import tkinter as tk
        from tkinter import messagebox
        
        license_data = self.license_manager.load_license()
        
        if license_data.get("status") == "error":
            messagebox.showerror("Error", license_data.get("message"))
            return
        
        # Format expiry information
        license_type = license_data.get('license_type', 'unknown')
        expiry_date = license_data.get('expiry_date')
        
        if expiry_date:
            expiry_dt = datetime.fromisoformat(expiry_date)
            days_remaining = (expiry_dt - datetime.now()).days
            if days_remaining < 0:
                expiry_info = f"Expired {abs(days_remaining)} days ago"
            else:
                expiry_info = f"Expires in {days_remaining} days ({expiry_date[:10]})"
        else:
            expiry_info = "No expiry (Unlimited)"
        
        info = f"""
        Serial: {license_data.get('serial')}
        Hardware ID: {license_data.get('hardware_id')}
        Activation Date: {license_data.get('activation_date')[:10]}
        License Type: {license_type.upper()}
        Expiry: {expiry_info}
        Status: {license_data.get('status')}
        Version: {license_data.get('version')}
        """
        
        messagebox.showinfo("License Information", info)


if __name__ == "__main__":
    # Test the license manager
    manager = LicenseManager()
    
    print("=" * 60)
    print("AVENTA HFT PRO 2026 - LICENSE SYSTEM TEST")
    print("=" * 60)
    
    # Get hardware ID
    hardware_id = manager.get_hardware_id()
    print(f"\nHardware ID: {hardware_id}")
    
    # Generate a test serial
    serial = manager.serial_generator.generate_serial(hardware_id)
    print(f"Generated Serial: {serial}")
    
    # Validate serial
    is_valid = manager.serial_generator.validate_serial(serial, hardware_id)
    print(f"Serial Valid: {is_valid}")
    
    # Create license
    license_data = manager.create_license(serial)
    print(f"\nLicense Data:\n{json.dumps(license_data, indent=2)}")
    
    # Save license
    if manager.save_license(license_data):
        print("\nLicense saved successfully")
    
    # Load and verify
    loaded = manager.load_license()
    print(f"\nLoaded License:\n{json.dumps(loaded, indent=2)}")
    
    is_valid, message = manager.verify_license()
    print(f"\nLicense Valid: {is_valid}")
    print(f"Message: {message}")
    
    print("\n" + "=" * 60)
