"""
License activation handler for Aventa HFT Pro
This module integrates license check at program startup
"""

import tkinter as tk
from tkinter import messagebox
import sys
from datetime import datetime, timedelta
from license_manager import LicenseManager, LicenseDialog


class LicenseCheckWindow:
    """Splash screen for license verification"""
    
    def __init__(self, root=None):
        """Initialize license check window"""
        self.license_manager = LicenseManager()
        self.root = root
        self.window = None
        self.is_licensed = False
    
    def check_license(self) -> bool:
        """
        Check if software is licensed
        If not, show activation dialog
        Returns True if licensed, False otherwise
        """
        # Try to verify existing license
        is_valid, message = self.license_manager.verify_license()
        
        if is_valid:
            # License is valid - show expiry info if applicable
            license_data = self.license_manager.load_license()
            license_type = license_data.get('license_type', 'unknown')
            expiry_date = license_data.get('expiry_date')
            
            if expiry_date:
                expiry_dt = datetime.fromisoformat(expiry_date)
                days_remaining = (expiry_dt - datetime.now()).days
                print(f"✅ License verified: {message}")
                print(f"   Type: {license_type}")
                print(f"   Expires in: {days_remaining} days ({expiry_date[:10]})")
                
                # Show warning if expiring soon (3 days or less)
                if 0 < days_remaining <= 3:
                    messagebox.showwarning(
                        "License Expiring Soon",
                        f"Your {license_type} license will expire in {days_remaining} days.\n\n"
                        f"Please renew your license to continue using the software."
                    )
            else:
                print(f"✅ License verified: {message}")
                print(f"   Type: Unlimited (No expiry)")
            
            self.is_licensed = True
            return True
        
        # No valid license - show activation dialog
        print(f"❌ License check failed: {message}")
        
        if not self.root:
            # Create minimal root for dialog
            self.root = tk.Tk()
            self.root.withdraw()
        
        # Show activation dialog
        dialog = LicenseDialog(self.root, self.license_manager)
        result = dialog.show_activation_dialog()
        
        if result:
            self.is_licensed = True
            return True
        else:
            # User canceled activation
            messagebox.showerror(
                "License Required",
                "This software requires activation to run.\n\n"
                "The application will now close."
            )
            return False
    
    def show_splash_screen(self):
        """Show splash screen during license check"""
        self.window = tk.Tk()
        self.window.title("Aventa HFT Pro 2026 - License Verification")
        self.window.geometry("500x250")
        self.window.resizable(False, False)
        self.window.configure(bg="#1a1a1a")
        
        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Content
        frame = tk.Frame(self.window, bg="#1a1a1a")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(
            frame,
            text="🚀 AVENTA HFT PRO 2026",
            font=("Arial", 18, "bold"),
            bg="#1a1a1a",
            fg="#4CAF50"
        )
        title.pack(pady=(0, 20))
        
        status = tk.Label(
            frame,
            text="Verifying License...",
            font=("Arial", 12),
            bg="#1a1a1a",
            fg="#FFF"
        )
        status.pack(pady=(0, 20))
        
        # Loading animation
        progress_frame = tk.Frame(frame, bg="#1a1a1a", height=30)
        progress_frame.pack(fill=tk.X, pady=10)
        
        # Simple loading dots animation
        self.loading_label = tk.Label(
            progress_frame,
            text="⏳ Checking license...",
            font=("Arial", 10),
            bg="#1a1a1a",
            fg="#4CAF50"
        )
        self.loading_label.pack()
        
        self.window.update()
        
        return self.window
    
    def close_splash(self):
        """Close splash screen"""
        if self.window:
            self.window.destroy()
            self.window = None


def enforce_license_on_startup(root=None) -> bool:
    """
    Call this at program startup to enforce license check
    
    Args:
        root: Optional Tkinter root window
    
    Returns:
        True if licensed and program should continue, False otherwise
    """
    license_check = LicenseCheckWindow(root)
    
    # First, try to verify existing license (quick check, no UI)
    is_valid, message = license_check.license_manager.verify_license()
    
    if is_valid:
        # License exists and is valid - proceed immediately
        print(f"✅ License verified: {message}")
        return True
    
    # No valid license found - show activation dialog
    print(f"⚠️ License check failed: {message}")
    print("💬 Showing license activation dialog...")
    
    # Create root window for dialog (VISIBLE, NOT WITHDRAWN)
    if not root:
        root = tk.Tk()
        # Don't withdraw - keep visible so dialog appears properly
        root.geometry("0x0+0+0")  # Move off-screen instead
        root.attributes('-alpha', 0)  # Make transparent
    
    try:
        # Show activation dialog directly
        dialog = LicenseDialog(root, license_check.license_manager)
        result = dialog.show_activation_dialog()
        
        if result:
            # User activated license successfully
            print("✅ License activated successfully!")
            # Only destroy if it's our root (not provided by caller)
            if root and not hasattr(root, '_provided_root'):
                try:
                    root.destroy()
                except:
                    pass  # Already destroyed or error - ignore
            return True
        else:
            # User cancelled activation
            print("❌ User cancelled license activation")
            # Only destroy if it's our root (not provided by caller)
            if root and not hasattr(root, '_provided_root'):
                try:
                    root.destroy()
                except:
                    pass  # Already destroyed or error - ignore
            return False
    
    except Exception as e:
        print(f"❌ Error during license activation: {e}")
        import traceback
        traceback.print_exc()
        # Only destroy if it's our root (not provided by caller)
        if root and not hasattr(root, '_provided_root'):
            try:
                root.destroy()
            except:
                pass  # Already destroyed or error - ignore
        return False


if __name__ == "__main__":
    # Test license check
    result = enforce_license_on_startup()
    print(f"License check result: {result}")
    
    if result:
        print("✅ Program can now run")
    else:
        print("❌ Program will exit")
        sys.exit(1)
