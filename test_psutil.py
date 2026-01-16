import psutil
from datetime import datetime

print("=== Testing psutil ===")
print(f"CPU: {psutil.cpu_percent(interval=0.1)}%")

ram = psutil.virtual_memory()
print(f"RAM: {ram.percent}% ({ram.used/(1024**3):.1f}/{ram.total/(1024**3):.1f} GB)")

disk = psutil.disk_usage('/')
print(f"Disk: {disk.percent}% ({disk.used/(1024**3):.0f}/{disk.total/(1024**3):.0f} GB)")

net = psutil.net_io_counters()
print(f"Network:  Sent={net.bytes_sent/(1024**2):.1f} MB, Recv={net.bytes_recv/(1024**2):.1f} MB")

print("\n✅ psutil is working correctly!")