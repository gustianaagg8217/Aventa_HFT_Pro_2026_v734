import tkinter as tk
import psutil

root = tk.Tk()
root.geometry("300x200")

label = tk.Label(root, text="Testing.. .", font=("Segoe UI", 10))
label.pack(pady=20)

def update():
    try:
        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)
        
        # Test dengan . format()
        text = "RAM: {:.1f}% ({:.1f}/{:.1f} GB)".format(
            ram. percent, ram_used_gb, ram_total_gb
        )
        label.config(text=text)
        print(f"✅ Update success: {text}")
    except Exception as e:
        label.config(text=f"Error: {e}")
        print(f"❌ Error: {e}")
    
    root.after(1000, update)

update()
root.mainloop()