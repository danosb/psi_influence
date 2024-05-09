import usb.backend.libusb1
import usb.core

# Set the path to the libusb backend .dylib file you found with brew (brew list libusb)
backend = usb.backend.libusb1.get_backend(find_library=lambda x: "/opt/homebrew/Cellar/libusb/1.0.27/lib/libusb-1.0.0.dylib")
print(backend)

# Continue with your usb.core or pyftdi functions as planned
