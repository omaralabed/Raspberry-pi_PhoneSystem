# Pico 2 Audio Interface - Quick Start Guide

## What You're Building

A **USB audio device** that converts your Raspberry Pi's USB audio into 8 balanced XLR outputs with 2-wire party line capability (simultaneous send/receive on same connector).

**Cost:** ~$150 | **Time:** 2-4 weeks | **Difficulty:** Intermediate

---

## Shopping List (Order First!)

### Essential Components - Order from DigiKey/Mouser/Amazon

```
☐ 1× Raspberry Pi Pico 2 (RP2350B)             $5
☐ 4× PCM5142 Stereo DAC Breakout               $32 total
☐ 4× PCM1863 Stereo ADC Breakout               $48 total
☐ 8× 600:600Ω Audio Transformer                $40 total
☐ 8× XLR Female Panel Mount                    $16 total
☐ 16× 470Ω Resistors (1% tolerance)            $2
☐ 16× 10µF Electrolytic Capacitors (100V)      $4
☐ 1× Prototype PCB or breadboard               $10
☐ 1× Metal Enclosure                           $15
☐ 1× USB-C cable (Pico 2 to Pi)                $5

                                    TOTAL: ~$177
```

### Tools You'll Need
- Soldering iron & solder
- Wire strippers
- Multimeter
- Breadboard (for testing)
- Computer with USB port

---

## Week 1: Get Firmware Running

### Day 1-2: Development Environment Setup

1. **Install Pico SDK:**
```bash
cd ~/
git clone https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
echo 'export PICO_SDK_PATH=~/pico-sdk' >> ~/.bashrc
source ~/.bashrc
```

2. **Install Build Tools:**
```bash
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi \
                 libstdc++-arm-none-eabi-newlib build-essential
```

3. **Clone TinyUSB Examples:**
```bash
cd ~/
git clone https://github.com/hathach/tinyusb.git
cd tinyusb/examples/device/audio_test
```

### Day 3-4: Basic USB Audio Test

4. **Build USB Audio Example:**
```bash
mkdir build && cd build
cmake .. -DFAMILY=rp2040 -DBOARD=pico2
make
```

5. **Flash to Pico 2:**
- Hold BOOTSEL button on Pico 2
- Plug USB cable into computer
- Copy `audio_test.uf2` to Pico drive
- Pico will reboot as USB audio device!

6. **Test on Your Pi:**
```bash
# On Raspberry Pi
aplay -l
# Should see: "USB Audio Device"

# Test audio output
speaker-test -D hw:X,0 -c 2 -t sine
```

**🎉 Milestone 1: Basic USB audio working!**

---

## Week 2: Add PIO I2S Output

### Day 5-7: Single Channel DAC

7. **Wire First DAC (PCM5142):**
```
Pico 2          PCM5142 DAC
GPIO 0  ───────→ BCK  (Bit Clock)
GPIO 1  ───────→ LRCK (L/R Clock)
GPIO 2  ───────→ DIN  (Data In)
3.3V    ───────→ VCC
GND     ───────→ GND
                 AOUT ──→ Amplifier/Speaker
```

8. **Write PIO I2S Code:**

Create `src/i2s_output.pio`:
```c
.program i2s_out
.side_set 2

.wrap_target
    out pins, 1   side 0b10
    out pins, 1   side 0b11
.wrap
```

9. **Test Audio Output:**
```bash
# Should hear 1kHz sine wave from DAC
```

**🎉 Milestone 2: PIO I2S working!**

---

## Week 3: Scale to 8 Channels (TDM)

### Day 8-10: TDM Configuration

10. **Wire All 4 DACs in TDM Mode:**
```
All DACs share same clock:
Pico GPIO 0 → BCK  (all 4 DACs)
Pico GPIO 1 → LRCK (all 4 DACs)
Pico GPIO 2 → DIN  (all 4 DACs)

I2C for configuration:
Pico GPIO 4 → SDA (all 4 DACs)
Pico GPIO 5 → SCL (all 4 DACs)
```

11. **Configure TDM via I2C:**
```c
// Set each DAC to different TDM slot
pcm5142_set_tdm_slot(dac1, 0);  // Channels 1-2
pcm5142_set_tdm_slot(dac2, 2);  // Channels 3-4
pcm5142_set_tdm_slot(dac3, 4);  // Channels 5-6
pcm5142_set_tdm_slot(dac4, 6);  // Channels 7-8
```

12. **Update USB Descriptor for 8 Channels:**
```c
#define AUDIO_CHANNELS 8
```

**🎉 Milestone 3: All 8 output channels working!**

---

## Week 4: Add Input (ADC) for Party Line

### Day 11-14: Bidirectional Audio

13. **Wire 4 ADCs (PCM1863) in TDM:**
```
Similar to DACs, but for input
Pico GPIO 6 → BCK  (ADC clock)
Pico GPIO 7 → LRCK (ADC clock)
Pico GPIO 8 → DOUT (ADC data to Pico)
```

14. **Add PIO I2S Input:**

Create `src/i2s_input.pio`:
```c
.program i2s_in
.side_set 2

.wrap_target
    in pins, 1    side 0b10
    in pins, 1    side 0b11
.wrap
```

15. **Test Loopback:**
```bash
# Audio from microphone → ADC → Pico → DAC → Speaker
```

**🎉 Milestone 4: Bidirectional audio working!**

---

## Week 5: Party Line Transformers

### Day 15-18: Hybrid Circuit

16. **Build One Hybrid Circuit:**
```
       DAC Out
          │
       470Ω R1
          │
          ├────→ Transformer Primary ──→ XLR Pin 2
          │         600:600Ω             XLR Pin 3
       10µF C1                           XLR Pin 1 (GND)
          │
       470Ω R2
          │
       ADC In
```

17. **Test Transformer:**
- Connect function generator to DAC side
- Measure XLR output with oscilloscope
- Should see balanced 600Ω signal

18. **Verify No Echo:**
- Feed test signal to DAC
- ADC should NOT receive it (hybrid nulling works)
- External signal to XLR should reach ADC

19. **Build All 8 Channels:**
- Repeat circuit 8 times
- Mount transformers on prototype board
- Wire to XLR panel connectors

**🎉 Milestone 5: Party line working!**

---

## Week 6: Integration with Phone System

### Day 19-21: Connect to Main Pi

20. **Physical Connection:**
```
Raspberry Pi 4/5 ──[USB Cable]──→ Pico 2 Interface
Pico 2 ──[8 XLR Cables]──→ Party Line Headsets
```

21. **Update Phone System Config:**

Edit `/home/procomm/ProComm/config/audio_config.json`:
```json
{
  "audio_device_name": "Pico2 Party Line",
  "num_outputs": 8,
  "num_inputs": 8,
  "sample_rate": 48000,
  "bidirectional": true,
  "party_line": {
    "enabled": true,
    "xlr_mode": "2-wire"
  }
}
```

22. **Test with Phone Call:**
```bash
cd ~/ProComm
python3 main.py
# Make test call
# Verify audio in/out on XLR
```

**🎉 Milestone 6: Full system integration complete!**

---

## Troubleshooting

### USB Device Not Recognized
- Check USB cable (must support data)
- Verify TinyUSB descriptor is correct
- Check `dmesg` on Pi for USB errors

### No Audio Output
- Verify I2S clock signals with oscilloscope
- Check DAC power (3.3V on VCC pin)
- Verify PIO state machine is running

### Audio Quality Issues
- Check sample rate (must match: 48kHz)
- Verify bit clock = 48kHz × 32 × 2 = 3.072MHz
- Check for ground loops

### Echo/Feedback on Party Line
- Adjust hybrid resistor values (try 390Ω or 560Ω)
- Verify transformer polarity
- Check null network capacitor (try 4.7µF or 22µF)

### Only Some Channels Work
- Check I2C addresses (each DAC/ADC needs unique address)
- Verify TDM slot configuration
- Check solder connections

---

## Testing Checklist

Before declaring victory:

```
☐ USB device enumerates on Pi
☐ All 8 output channels produce audio
☐ All 8 input channels receive audio
☐ No echo/feedback with transformers
☐ 600Ω balanced output measured
☐ Phone call audio quality acceptable
☐ Latency <20ms measured
☐ Multiple XLRs can connect together (party line)
☐ No ground loop hum
☐ All channels work simultaneously
```

---

## Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Latency** | <10ms | Loopback test with oscilloscope |
| **THD** | <0.1% | Audio analyzer |
| **Frequency Response** | 20Hz-20kHz ±1dB | Sweep test |
| **Output Impedance** | 600Ω ±5% | Multimeter |
| **Crosstalk** | <-60dB | Signal on ch1, measure ch2 |

---

## When You're Done

You'll have:
- ✅ 8-channel USB audio device
- ✅ Professional 2-wire party line interface
- ✅ Same XLR for send/receive
- ✅ Full duplex operation
- ✅ $150 device that replaces $5,000 commercial gear

**Post photos to Reddit r/raspberry_pi!** 📸

---

## Next: Build the Enclosure

See `docs/PICO2_ENCLOSURE_DESIGN.md` for:
- PCB layout files
- 3D printable enclosure
- Panel layout for XLR connectors
- Cable management
- Professional finishing

---

## Need Help?

- **Hardware issues:** Check wiring diagram
- **Software issues:** See `PICO2_AUDIO_INTERFACE.md`
- **Party line issues:** Check hybrid circuit
- **Integration:** See main Phone System docs

**You've got this! 🎯**
