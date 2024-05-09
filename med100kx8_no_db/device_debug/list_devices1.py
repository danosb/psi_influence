import usb.core
import usb.backend.libusb1

backend = usb.backend.libusb1.get_backend(find_library=lambda x: "/opt/homebrew/Cellar/libusb/1.0.27/lib/libusb-1.0.0.dylib")
devices = usb.core.find(find_all=True, backend=backend)
for device in devices:
    print(device)
