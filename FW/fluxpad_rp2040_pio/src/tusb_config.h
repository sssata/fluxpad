#pragma once

#ifdef __cplusplus
extern "C" {
#endif

//--------------------------------------------------------------------
// COMMON CONFIGURATION
//--------------------------------------------------------------------
#define CFG_TUSB_RHPORT0_MODE OPT_MODE_DEVICE

// Enable device stack
#define CFG_TUD_ENABLED 1

// Enable host stack with pio-usb if Pico-PIO-USB library is available
#if __has_include("pio_usb.h")
#define CFG_TUH_ENABLED 1
#define CFG_TUH_RPI_PIO_USB 1
#endif

#ifndef CFG_TUSB_MCU
#define CFG_TUSB_MCU OPT_MCU_RP2040
#endif
#define CFG_TUSB_OS OPT_OS_PICO

#ifndef CFG_TUSB_DEBUG
#define CFG_TUSB_DEBUG 0
#endif

#define CFG_TUSB_MEM_SECTION
#define CFG_TUSB_MEM_ALIGN TU_ATTR_ALIGNED(4)

//--------------------------------------------------------------------
// Device Configuration
//--------------------------------------------------------------------

#define CFG_TUD_ENDOINT0_SIZE 64

#define CFG_TUD_CDC 1
#define CFG_TUD_MSC 0
#define CFG_TUD_HID 1
#define CFG_TUD_MIDI 0
#define CFG_TUD_VENDOR 0

// CDC FIFO size of TX and RX
#define CFG_TUD_CDC_RX_BUFSIZE 256
#define CFG_TUD_CDC_TX_BUFSIZE 256

// MSC Buffer size of Device Mass storage
// #define CFG_TUD_MSC_EP_BUFSIZE 512

// HID buffer size Should be sufficient to hold ID (if any) + Data
#define CFG_TUD_HID_EP_BUFSIZE 64

// MIDI FIFO size of TX and RX
// #define CFG_TUD_MIDI_RX_BUFSIZE 128
// #define CFG_TUD_MIDI_TX_BUFSIZE 128

// Vendor FIFO size of TX and RX
// #define CFG_TUD_VENDOR_RX_BUFSIZE 64
// #define CFG_TUD_VENDOR_TX_BUFSIZE 64

//--------------------------------------------------------------------
// Host Configuration
//--------------------------------------------------------------------

// Size of buffer to hold descriptors and other data used for enumeration
#define CFG_TUH_ENUMERATION_BUFSIZE 256

// Number of hub devices
#define CFG_TUH_HUB 1

// max device support (excluding hub device): 1 hub typically has 4 ports
#define CFG_TUH_DEVICE_MAX (3 * CFG_TUH_HUB + 1)

// Enable tuh_edpt_xfer() API
// #define CFG_TUH_API_EDPT_XFER       1

// Number of mass storage
#define CFG_TUH_MSC 1

// Number of HIDs
// typical keyboard + mouse device can have 3,4 HID interfaces
#define CFG_TUH_HID (3 * CFG_TUH_DEVICE_MAX)

// Number of CDC interfaces
// FTDI and CP210x are not part of CDC class, only to re-use CDC driver API
#define CFG_TUH_CDC 1
#define CFG_TUH_CDC_FTDI 1
#define CFG_TUH_CDC_CP210X 1

// RX & TX fifo size
#define CFG_TUH_CDC_RX_BUFSIZE 128
#define CFG_TUH_CDC_TX_BUFSIZE 128

// Set Line Control state on enumeration/mounted:
// DTR ( bit 0), RTS (bit 1)
#define CFG_TUH_CDC_LINE_CONTROL_ON_ENUM 0x03

// Set Line Coding on enumeration/mounted, value for cdc_line_coding_t
// bit rate = 115200, 1 stop bit, no parity, 8 bit data width
// This need Pico-PIO-USB at least 0.5.1
#define CFG_TUH_CDC_LINE_CODING_ON_ENUM                                        \
  { 115200, CDC_LINE_CONDING_STOP_BITS_1, CDC_LINE_CODING_PARITY_NONE, 8 }

#ifdef __cplusplus
}
#endif

