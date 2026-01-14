# Raspberry Pi Pico 2 - 8-Channel Party Line Audio Interface

## Overview

Custom USB audio device for the Phone System using Raspberry Pi Pico 2 (RP2350) with PIO-based I2S audio and hybrid transformers for 2-wire party line XLR connections.

**Key Features:**
- ✅ 8 independent bidirectional audio channels
- ✅ USB Audio Class device (plug & play)
- ✅ 2-wire party line on same XLR (simultaneous send/receive)
- ✅ PIO hardware acceleration (zero CPU overhead)
- ✅ 600Ω balanced XLR outputs
- ✅ Battery backup capable
- ✅ Total cost: ~$100-150 (vs $5,000 commercial)

---

## Hardware Specifications

### Raspberry Pi Pico 2 (RP2350B)
- **Dual ARM Cortex-M33 @ 150MHz**
- **2 PIO blocks** with 4 state machines each (8 total)
- **264KB SRAM** - plenty for audio buffers
- **USB 1.1 Device** - Full Speed (12 Mbps)
- **26 GPIO pins** - enough for 8 channels I2S

### Audio Specifications
- **Sample Rate:** 48 kHz (professional standard)
- **Bit Depth:** 16-bit (CD quality)
- **Channels:** 8 output + 8 input (full duplex)
- **Latency:** <10ms (PIO hardware timing)
- **Impedance:** 600Ω balanced (party line standard)

---

## Bill of Materials (BOM)

### Core Components

| Component | Qty | Unit Cost | Total | Notes |
|-----------|-----|-----------|-------|-------|
| **Raspberry Pi Pico 2** | 1 | $5.00 | $5.00 | RP2350B version |
| **PCM5102A DAC Module** | 8 | $2.50 | $20.00 | I2S 32-bit DAC |
| **PCM1808 ADC Module** | 8 | $3.50 | $28.00 | I2S 24-bit ADC |
| **600:600Ω Transformer** | 8 | $5.00 | $40.00 | Audio isolation |
| **XLR Female Panel Mount** | 8 | $2.00 | $16.00 | 3-pin balanced |
| **Resistors (470Ω, 1%)** | 16 | $0.10 | $1.60 | Hybrid network |
| **Capacitors (10µF, 100V)** | 16 | $0.20 | $3.20 | DC blocking |
| **Prototype PCB** | 1 | $10.00 | $10.00 | Or custom PCB |
| **Enclosure** | 1 | $15.00 | $15.00 | Metal case |
| **Power Supply (5V 2A)** | 1 | $8.00 | $8.00 | USB-C or barrel |

**TOTAL:** ~**$146.80**

### Optional Components
- **LiPo Battery (3.7V 2000mAh):** $12 - Battery backup
- **Battery charging circuit:** $5 - Auto charge/switch
- **Status LEDs:** $2 - Channel activity indicators
- **Potentiometers:** $8 - Level adjustment per channel

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 4/5                            │
│                  (Phone System Main CPU)                       │
│                                                                │
│  8 Phone Lines → Audio Routing → USB Audio Out (8 ch)         │
│                                   USB Audio In  (8 ch)         │
└──────────────────────────┬─────────────────────────────────────┘
                           │ USB 2.0 Cable
                           ▼
┌────────────────────────────────────────────────────────────────┐
│              Raspberry Pi Pico 2 (RP2350)                      │
│                 USB Audio Class Device                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              PIO State Machines                          │ │
│  │  ┌────────┬────────┬────────┬────────┐                  │ │
│  │  │ PIO0-0 │ PIO0-1 │ PIO0-2 │ PIO0-3 │  I2S OUT (DAC)   │ │
│  │  └────────┴────────┴────────┴────────┘                  │ │
│  │  ┌────────┬────────┬────────┬────────┐                  │ │
│  │  │ PIO1-0 │ PIO1-1 │ PIO1-2 │ PIO1-3 │  I2S IN  (ADC)   │ │
│  │  └────────┴────────┴────────┴────────┘                  │ │
│  └──────────────────────────────────────────────────────────┘ │
│                           │                                    │
└───────────────────────────┼────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │ 8 Bidirectional Audio Channels        │
        └───────────────────┬───────────────────┘
                            │
    ┌───────────────────────┴───────────────────────────────┐
    │     Per Channel (×8):                                 │
    │                                                       │
    │  DAC ──→ Hybrid Transformer ←──→ XLR Connector       │
    │  ADC ←──┘        ↕              (2-wire party line)   │
    │           Pins 2+3 (balanced)                         │
    └───────────────────────────────────────────────────────┘
```

---

## GPIO Pin Assignment

### Channel 1 (Line 1)
```
GPIO 0:  I2S_BCLK_OUT_1   (DAC Bit Clock)
GPIO 1:  I2S_LRCLK_OUT_1  (DAC L/R Clock)
GPIO 2:  I2S_DATA_OUT_1   (DAC Data)
GPIO 3:  I2S_BCLK_IN_1    (ADC Bit Clock)
GPIO 4:  I2S_LRCLK_IN_1   (ADC L/R Clock)
GPIO 5:  I2S_DATA_IN_1    (ADC Data)
```

### Channels 2-7 (Lines 2-7)
```
Similar pattern: 6 GPIO per channel
Total: 6 × 7 = 42 GPIO needed
```

### **Problem: Pico 2 only has 26 GPIO!**

**Solution: Use TDM (Time Division Multiplexing)**
- Share clock signals across multiple channels
- Reduces to ~12 GPIO total
- Requires TDM-capable DAC/ADCs

---

## Revised Design: TDM Mode

### Using PCM186x (TDM ADC) and PCM512x (TDM DAC)

```
Pico 2 GPIO:
├─ GPIO 0-2:   Master I2S/TDM for all 8 DACs (shared clock)
├─ GPIO 3-5:   Master I2S/TDM for all 8 ADCs (shared clock)
├─ GPIO 6-13:  I2C for DAC/ADC configuration
└─ GPIO 14-15: Status LEDs
```

**New BOM (TDM version):**
- Replace PCM5102A with **PCM5142** (Stereo TDM DAC) × 4 = $32
- Replace PCM1808 with **PCM1863** (Stereo TDM ADC) × 4 = $48
- Total channels: 4 stereo pairs = 8 mono channels

---

## Circuit Schematic (Per Channel)

```
Pico 2                         Party Line XLR
GPIO ──→ [I2S] ──→ PCM5142 ──→ 600:600Ω ──→ Pin 2/3
                    (DAC)      Transformer    (balanced)
                                   ↕
GPIO ←── [I2S] ←── PCM1863 ←── Hybrid ←───── Pin 2/3
                    (ADC)        Network      (same pins!)
                                              Pin 1 = GND
```

### Hybrid Transformer Network

```
DAC Out ──┬─── 470Ω ───┬──→ Transformer Primary ──→ XLR Pin 2
          │            │
       10µF Cap     Null Network
          │            │
ADC In ───┴─── 470Ω ───┴──→ Transformer Secondary ─→ XLR Pin 3
                                                      
Ground ──────────────────────────────────────────────→ XLR Pin 1
```

**This prevents echo/feedback while allowing bidirectional audio**

---

## PIO Firmware Structure

### PIO Program for I2S Output (DAC)

```c
.program i2s_out
.side_set 2

; Bit clock on side-set pin 0
; L/R clock on side-set pin 1

.wrap_target
    out pins, 1   side 0b10   ; Output data bit, BCLK low, LRCLK high (left)
    out pins, 1   side 0b11   ; Output data bit, BCLK high, LRCLK high
    ; ... 30 more bits for 32-bit audio frame ...
    out pins, 1   side 0b00   ; Output data bit, BCLK low, LRCLK low (right)
    out pins, 1   side 0b01   ; Output data bit, BCLK high, LRCLK low
.wrap
```

### PIO Program for I2S Input (ADC)

```c
.program i2s_in
.side_set 2

; Read audio data from ADC via I2S

.wrap_target
    in pins, 1    side 0b10   ; Read data bit, generate clocks
    in pins, 1    side 0b11
    ; ... continue for full frame ...
.wrap
```

### Main Firmware (C)

```c
#include "pico/stdlib.h"
#include "hardware/pio.h"
#include "hardware/dma.h"
#include "tusb.h"  // TinyUSB for USB audio

// Audio buffers
#define BUFFER_SIZE 512
int16_t audio_out_buffer[8][BUFFER_SIZE];  // 8 channels output
int16_t audio_in_buffer[8][BUFFER_SIZE];   // 8 channels input

// USB Audio callbacks
void tud_audio_rx_done_cb(uint8_t rhport, uint16_t n_bytes) {
    // Receive audio from Pi → DMA to PIO → DACs
    tud_audio_read(audio_out_buffer, sizeof(audio_out_buffer));
    // DMA transfer to PIO state machines
}

void tud_audio_tx_done_cb(uint8_t rhport) {
    // Send audio from ADCs → PIO → DMA → USB to Pi
    tud_audio_write(audio_in_buffer, sizeof(audio_in_buffer));
}

int main() {
    // Initialize PIO for I2S
    setup_pio_i2s();
    
    // Initialize USB Audio Class device
    tusb_init();
    
    // Main loop
    while (1) {
        tud_task();  // TinyUSB task
    }
}
```

---

## USB Audio Descriptor

The Pico 2 will identify as:

```
Device: "Pico2 8-Channel Party Line Interface"
Class: Audio Device Class (UAC2)
Outputs: 8 channels @ 48kHz/16-bit
Inputs: 8 channels @ 48kHz/16-bit
Latency: ~10ms (configurable)
```

Your Raspberry Pi will see it as a standard USB sound card!

---

## Configuration on Main Phone System

### Update audio_config.json

```json
{
  "audio_device_name": "Pico2 Party Line",
  "audio_device_index": null,
  "num_outputs": 8,
  "num_inputs": 8,
  "sample_rate": 48000,
  "buffer_size": 256,
  "latency": "low",
  "bidirectional": true,
  "default_routing": {
    "line_1": 1,
    "line_2": 2,
    "line_3": 3,
    "line_4": 4,
    "line_5": 5,
    "line_6": 6,
    "line_7": 7,
    "line_8": 8
  },
  "party_line": {
    "enabled": true,
    "xlr_mode": "2-wire",
    "impedance": "600ohm",
    "hybrid_enabled": true
  }
}
```

### ALSA Detection (on Pi)

```bash
aplay -l
# Should show:
# card 2: Pico2PartyLine [Pico2 8-Channel Party Line Interface]
#   device 0: USB Audio [USB Audio]
#   Subdevices: 1/1
```

---

## Development Steps

### Phase 1: Basic USB Audio (Week 1)
- [x] Set up Pico SDK
- [ ] Implement TinyUSB audio device
- [ ] Test 2-channel stereo output
- [ ] Verify USB enumeration on Pi

### Phase 2: PIO I2S (Week 2)
- [ ] Write PIO I2S output program
- [ ] Write PIO I2S input program
- [ ] Test with single DAC/ADC pair
- [ ] Measure latency

### Phase 3: Multi-Channel TDM (Week 3)
- [ ] Implement TDM for 8 channels
- [ ] Configure PCM512x/PCM186x via I2C
- [ ] Test all 8 channels
- [ ] DMA optimization

### Phase 4: Hybrid Transformers (Week 4)
- [ ] Design hybrid circuit
- [ ] Build prototype for 1 channel
- [ ] Test echo cancellation
- [ ] Scale to 8 channels

### Phase 5: Integration (Week 5)
- [ ] Connect to Phone System Pi
- [ ] Update audio_router.py for bidirectional
- [ ] Test real phone calls with party line
- [ ] Performance optimization

### Phase 6: Enclosure (Week 6)
- [ ] Design PCB layout
- [ ] Order PCB manufacturing
- [ ] 3D print/metal enclosure
- [ ] Final assembly and testing

---

## Testing Checklist

### Hardware Tests
- [ ] USB enumeration on Raspberry Pi
- [ ] All 8 DAC outputs producing audio
- [ ] All 8 ADC inputs receiving audio
- [ ] Hybrid transformers isolating send/receive
- [ ] XLR connections balanced and working
- [ ] No ground loops or noise

### Software Tests
- [ ] USB Audio Class device recognized
- [ ] ALSA sees 8 output channels
- [ ] ALSA sees 8 input channels
- [ ] Phone System can route to all channels
- [ ] Bidirectional audio working
- [ ] Latency <10ms measured

### Party Line Tests
- [ ] Simultaneous send/receive on same XLR
- [ ] No echo or feedback
- [ ] 600Ω impedance correct
- [ ] Multiple party line units connected
- [ ] Audio quality acceptable
- [ ] Full duplex communication working

---

## Power Requirements

### USB Powered (Standard)
- Pico 2: 30mA idle, 100mA active
- 8× DACs: 8 × 10mA = 80mA
- 8× ADCs: 8 × 15mA = 120mA
- **Total: ~300mA @ 5V** (1.5W)
- ✅ USB 2.0 can provide 500mA - **sufficient!**

### Battery Backup (Optional)
- LiPo 3.7V 2000mAh
- 3.7V → 5V boost converter (500mA)
- Runtime: ~4-6 hours
- Auto-switch when USB disconnected

---

## Advantages Over Commercial Solutions

| Feature | Pico 2 DIY | Commercial | Savings |
|---------|-----------|------------|---------|
| **8-Channel I/O** | $147 | $3,000-5,000 | 95% |
| **2-Wire Party Line** | Yes | Yes | - |
| **USB Audio** | Yes | Yes | - |
| **Customizable** | Fully | Limited | - |
| **Battery Backup** | $20 extra | $500 extra | 96% |
| **Repair/Modify** | Easy | Impossible | - |
| **Open Source** | Yes | No | - |

---

## Resources

### Documentation
- [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk)
- [TinyUSB Audio Examples](https://github.com/hathach/tinyusb)
- [PIO I2S Examples](https://github.com/raspberrypi/pico-examples)

### Datasheets
- [RP2350 Datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- [PCM5142 DAC](https://www.ti.com/product/PCM5142)
- [PCM1863 ADC](https://www.ti.com/product/PCM1863)

### Community
- Raspberry Pi Forums - Pico section
- Discord: TinyUSB channel
- Reddit: r/raspberry_pi_projects

---

## Next Steps

1. **Order parts** - See BOM above
2. **Set up development environment** - Pico SDK + VSCode
3. **Start with Phase 1** - Basic USB audio
4. **Breadboard prototype** - Test single channel first
5. **Iterate and test** - Build up to 8 channels
6. **Integration** - Connect to Phone System

---

## Contact & Support

**Project:** Raspberry Pi Phone System - Party Line Interface
**Hardware:** Raspberry Pi Pico 2 (RP2350)
**License:** MIT (Open Source)

For questions or contributions, see main project README.

---

**Status:** Planning Phase
**Target Completion:** 6 weeks
**Budget:** ~$150 for 8-channel system
**Expected Performance:** Professional broadcast quality party line interface

🎯 **This will replace $5,000 of commercial gear for $150!**
