"""
License Validator - MANDATORY License Check
This module enforces that ALL program execution requires valid license
Cannot be bypassed or skipped - prevents program startup without activation
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from datetime import datetime

# ============================================================================
# STRICT LICENSE VALIDATION - NO BYPASSES
# ============================================================================

class LicenseValidator:
    """Strict license validator - program cannot run without valid license"""
    
    def __init__(self):
        self.is_valid = False
        self.error_message = ""
        self.license_data = None
    
    def validate(self) -> bool:
        """
        MANDATORY validation - must pass before any program code executes
        If validation fails, program MUST exit immediately
        """
        try:
            # Step 1: Try to import license manager
            try:
                from license_manager import LicenseManager
            except ImportError as e:
                self.error_message = f"License system unavailable: {str(e)}"
                print(f"❌ CRITICAL: {self.error_message}")
                return False
            
            # Step 2: Initialize license manager
            try:
                self.license_manager = LicenseManager()
            except Exception as e:
                self.error_message = f"Failed to initialize license manager: {str(e)}"
                print(f"❌ CRITICAL: {self.error_message}")
                return False
            
            # Step 3: Check if license exists and is valid
            try:
                is_valid, message = self.license_manager.verify_license()
                
                if not is_valid:
                    self.error_message = f"License invalid: {message}"
                    print(f"❌ License check failed: {self.error_message}")
                    return False
                
                # License is valid - get details
                self.license_data = self.license_manager.load_license()
                self.is_valid = True
                
                # Print license info
                license_type = self.license_data.get('license_type', 'unknown')
                expiry_date = self.license_data.get('expiry_date')
                
                if expiry_date:
                    from datetime import datetime
                    expiry_dt = datetime.fromisoformat(expiry_date)
                    days_remaining = (expiry_dt - datetime.now()).days
                    print(f"✅ License VALID: {license_type} (Expires in {days_remaining} days)")
                else:
                    print(f"✅ License VALID: {license_type} (Unlimited)")
                
                return True
                
            except Exception as e:
                self.error_message = f"License verification error: {str(e)}"
                print(f"❌ CRITICAL: {self.error_message}")
                return False
        
        except Exception as e:
            self.error_message = f"Unexpected license validation error: {str(e)}"
            print(f"❌ CRITICAL: {self.error_message}")
            return False
    
    def show_error_and_exit(self):
        """Show error dialog and force exit (cannot continue)"""
        # Create minimal root window for dialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        messagebox.showerror(
            "❌ LICENSE VALIDATION FAILED",
            f"This software requires activation to run.\n\n"
            f"Error: {self.error_message}\n\n"
            f"Please activate using the Serial Generator.\n"
            f"The application will now close."
        )
        
        root.destroy()
        sys.exit(1)
    
    def show_activation_dialog(self):
        """Show activation dialog if no valid license"""
        try:
            from license_check import enforce_license_on_startup
            
            # Create root for dialog
            root = tk.Tk()
            root.withdraw()
            
            # Show license check - this handles the dialog and cleanup internally
            result = enforce_license_on_startup(root)
            
            # enforce_license_on_startup already destroys root, so just handle the result
            if not result:
                # Need to create new root for error message since previous was destroyed
                error_root = tk.Tk()
                error_root.withdraw()
                messagebox.showerror(
                    "❌ ACTIVATION REQUIRED",
                    "License activation failed.\n\n"
                    "The application cannot run without a valid license.\n"
                    "Please try again or contact support."
                )
                error_root.destroy()
                sys.exit(1)
            
            # Activation successful - root already destroyed by enforce_license_on_startup
            return True
            
        except Exception as e:
            print(f"❌ Failed to show activation dialog: {e}")
            import traceback
            traceback.print_exc()
            
            # Try to show error with new root window
            try:
                error_root = tk.Tk()
                error_root.withdraw()
                messagebox.showerror(
                    "Error",
                    f"Failed to show license activation dialog.\n\n{str(e)}"
                )
                error_root.destroy()
            except:
                pass
            
            sys.exit(1)


def validate_license_or_exit():
    """
    MAIN VALIDATION FUNCTION
    
    Call this at VERY START of program (before any other imports or code)
    If validation fails, exits immediately with error message
    
    Returns:
        True if license is valid (program can continue)
        Never returns False - will exit instead
    """
    print("\n" + "="*70)
    print("🔐 AVENTA HFT PRO 2026 - LICENSE VALIDATION")
    print("="*70)
    
    validator = LicenseValidator()
    
    # Perform validation
    if validator.validate():
        print("="*70)
        print("✅ LICENSE VALIDATION PASSED - Program starting...\n")
        return True
    
    # Validation failed - try to show activation dialog
    print("\n⚠️ No valid license found - showing activation dialog...")
    
    try:
        validator.show_activation_dialog()
        # If user activated successfully, validate again
        if validator.validate():
            print("="*70)
            print("✅ LICENSE ACTIVATED - Program starting...\n")
            return True
        else:
            # Validation still failed
            print("❌ License validation failed even after activation attempt")
            validator.show_error_and_exit()
    
    except Exception as e:
        print(f"❌ Error during activation: {e}")
        validator.show_error_and_exit()


if __name__ == "__main__":
    # Test license validation
    if validate_license_or_exit():
        print("✅ License validation passed - program can proceed")
    else:
        print("❌ Program exit due to license validation failure")
