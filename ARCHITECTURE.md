# System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI PHONE SYSTEM - IFB/PL                      │
│                              Ubuntu 22.04 LTS                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          TOUCHSCREEN INTERFACE                              │
│  ┌─────────────────────────────────────┐  ┌──────────────────────────────┐ │
│  │         LINE STATUS PANEL           │  │     CONTROL PANEL            │ │
│  │                                     │  │                              │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │  Selected: Line 1            │ │
│  │  │LINE 1│ │LINE 2│ │LINE 3│ │LINE 4│  │  ┌─────┐ ┌─────┐ ┌─────┐   │ │
│  │  │ IFB  │ │ IFB  │ │ PL   │ │ PL   │  │  │  1  │ │  2  │ │  3  │   │ │
│  │  │🟢IDLE│ │🟢CONN│ │🟡DIAL│ │🟢IDLE│  │  └─────┘ └─────┘ └─────┘   │ │
│  │  │ 🔊   │ │Hang Up│ │ 🔊   │ │ 🔊   │  │  ┌─────┐ ┌─────┐ ┌─────┐   │ │
│  │  └──────┘ └──────┘ └──────┘ └──────┘  │  │  4  │ │  5  │ │  6  │   │ │
│  │                                     │  │  └─────┘ └─────┘ └─────┘   │ │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │  ┌─────┐ ┌─────┐ ┌─────┐   │ │
│  │  │LINE 5│ │LINE 6│ │LINE 7│ │LINE 8│  │  │  7  │ │  8  │ │  9  │   │ │
│  │  │ IFB  │ │ PL   │ │ PL   │ │ IFB  │  │  └─────┘ └─────┘ └─────┘   │ │
│  │  │🟢IDLE│ │🟢IDLE│ │🟢IDLE│ │🟢IDLE│  │  ┌─────┐ ┌─────┐ ┌─────┐   │ │
│  │  │ 🔊   │ │ 🔊   │ │ 🔊   │ │ 🔊   │  │  │  *  │ │  0  │ │  #  │   │ │
│  │  └──────┘ └──────┘ └──────┘ └──────┘  │  └─────┘ └─────┘ └─────┘   │ │
│  └─────────────────────────────────────┘  │                              │ │
│                                            │  [⌫ Back] [Clear]            │ │
│                                            │  ┌────────────────────────┐ │ │
│                                            │  │     📞 CALL            │ │ │
│                                            │  └────────────────────────┘ │ │
│                                            │                              │ │
│                                            │  🎧 IFB (Talent)             │ │
│                                            │  [Test IFB]                  │ │
│                                            │  📻 PL (Crew)                │ │
│                                            │  [Test PL]                   │ │
│                                            └──────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PYTHON APPLICATION LAYER                           │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  GUI (PyQt5)   │  │   SIP Engine     │  │   Audio Router           │  │
│  │                │  │   (PJSIP)        │  │   (PulseAudio)           │  │
│  │ - Main Window  │◄─┤                  │  │                          │  │
│  │ - Dialer Pad   │  │ - 8 SIP Accounts │  │ - IFB Routing (Ch 1-2)   │  │
│  │ - Line Status  │  │ - Call Manager   │◄─┤ - PL Routing (Ch 3-4)    │  │
│  │ - Audio Widget │  │ - Single Trunk   │  │ - Real-time Switching    │  │
│  └────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
         │                       │                          │
         ▼                       ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM/HARDWARE LAYER                             │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  X11/Wayland   │  │  Network Stack   │  │   ALSA/PulseAudio        │  │
│  │  Touchscreen   │  │  Ethernet/WiFi   │  │   USB Audio Driver       │  │
│  └────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
         │                       │                          │
         ▼                       ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PHYSICAL HARDWARE                                │
│                                                                             │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  7" Touchscreen│  │  Ethernet Port   │  │  USB Audio Interface     │  │
│  │  800x480       │  │  100/1000 Mbps   │  │  4+ Outputs              │  │
│  └────────────────┘  └──────────────────┘  └──────────┬───────────────┘  │
│                                                         │                   │
│  ┌─────────────────────────────────────────────────────┘                   │
│  │   Raspberry Pi 4/5                                                      │
│  │   - ARM64 CPU                                                           │
│  │   - 4-8GB RAM                                                           │
│  │   - Ubuntu 22.04 LTS                                                    │
│  └─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL CONNECTIONS                              │
│                                                                             │
│  INTERNET (SIP Provider)              AUDIO OUTPUTS                        │
│  ┌────────────────┐                   ┌──────────────────────────────┐    │
│  │  SIP Trunk     │◄─── Ethernet ───► │  USB Audio Interface         │    │
│  │  - Twilio      │                   │  ┌────────────────────────┐  │    │
│  │  - Vonage      │                   │  │ Output 1 (L) ──► IFB L │  │    │
│  │  - Bandwidth   │                   │  │ Output 2 (R) ──► IFB R │  │    │
│  │  - Others      │                   │  │ Output 3 (L) ──► PL L  │  │    │
│  │                │                   │  │ Output 4 (R) ──► PL R  │  │    │
│  │ Single Phone # │                   │  └────────────────────────┘  │    │
│  │ 8 Concurrent   │                   └──────────────────────────────┘    │
│  │ Lines          │                              │                         │
│  └────────────────┘                              ▼                         │
│                                        ┌──────────────────────┐            │
│                                        │   Production Mixer   │            │
│                                        │   or Headphones      │            │
│                                        └──────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                               CALL FLOW EXAMPLE
═══════════════════════════════════════════════════════════════════════════════

1. OPERATOR ACTIONS:
   ┌──────────────────────────────────────────────────────────────────┐
   │ [1] Select Line 3                                                │
   │ [2] Enter phone number: +1-555-1234                              │
   │ [3] Press CALL button                                            │
   │ [4] Click 🔊 to route to PL instead of IFB                       │
   └──────────────────────────────────────────────────────────────────┘

2. SYSTEM PROCESSING:
   ┌──────────────────────────────────────────────────────────────────┐
   │ GUI → SIP Engine: make_call(line_id=3, number="+15551234")      │
   │ SIP Engine → SIP Provider: INVITE sip:+15551234@provider.com    │
   │ SIP Provider → Destination: Call rings                           │
   │ Destination answers → Audio connected                            │
   │ GUI → Audio Router: route_line(3, AudioOutput.PL)               │
   │ Audio Router: Maps Line 3 audio to PL channels (3-4)            │
   └──────────────────────────────────────────────────────────────────┘

3. ACTIVE CALL:
   ┌──────────────────────────────────────────────────────────────────┐
   │ Line 3 Widget: 🟢 GREEN "Connected +15551234 (01:23)"           │
   │ Audio: Bidirectional RTP ↔ PL Output (Channels 3-4)             │
   │ Status: Can toggle IFB/PL anytime during call                    │
   └──────────────────────────────────────────────────────────────────┘

4. HANGUP:
   ┌──────────────────────────────────────────────────────────────────┐
   │ Operator presses "Hang Up" button                                │
   │ GUI → SIP Engine: hangup_call(line_id=3)                        │
   │ SIP Engine: Sends BYE message                                    │
   │ Line 3 returns to IDLE state (available)                         │
   └──────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
                          AUDIO ROUTING FLEXIBILITY
═══════════════════════════════════════════════════════════════════════════════

Each line can be independently routed to IFB or PL:

EXAMPLE CONFIGURATION:
┌────────┬──────────────────┬─────────────┬──────────────────────────────────┐
│ Line   │ Status           │ Route       │ Use Case                         │
├────────┼──────────────────┼─────────────┼──────────────────────────────────┤
│ Line 1 │ 🟢 CONNECTED     │ IFB (Blue)  │ Director talking to presenter    │
│ Line 2 │ 🟢 CONNECTED     │ IFB (Blue)  │ Producer talking to host         │
│ Line 3 │ 🟢 CONNECTED     │ PL (Orange) │ Stage manager coordinating       │
│ Line 4 │ 🟢 CONNECTED     │ PL (Orange) │ Technical director briefing crew │
│ Line 5 │ 🟢 IDLE          │ IFB (Blue)  │ Available                        │
│ Line 6 │ 🟢 IDLE          │ PL (Orange) │ Available                        │
│ Line 7 │ 🟢 IDLE          │ PL (Orange) │ Available                        │
│ Line 8 │ 🟢 IDLE          │ IFB (Blue)  │ Available                        │
└────────┴──────────────────┴─────────────┴──────────────────────────────────┘

AUDIO OUTPUT MIXING:
                    ┌─────────────────────┐
    Line 1 (IFB) ──►│                     │
    Line 2 (IFB) ──►│  IFB Mixer          ├──► Outputs 1-2 (Stereo)
    Line 5 (IFB) ──►│  (Channels 1-2)     │         │
    Line 8 (IFB) ──►│                     │         ▼
                    └─────────────────────┘    Talent Headphones
                                               
                    ┌─────────────────────┐
    Line 3 (PL)  ──►│                     │
    Line 4 (PL)  ──►│  PL Mixer           ├──► Outputs 3-4 (Stereo)
    Line 6 (PL)  ──►│  (Channels 3-4)     │         │
    Line 7 (PL)  ──►│                     │         ▼
                    └─────────────────────┘    Crew Headphones

═══════════════════════════════════════════════════════════════════════════════

KEY FEATURES:
✓ 8 simultaneous outgoing calls
✓ Single phone number (caller ID)
✓ Touchscreen control
✓ Real-time IFB/PL routing
✓ No incoming calls (production security)
✓ Lightweight & portable
✓ Professional audio quality
