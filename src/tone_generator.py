#!/usr/bin/env python3
"""
Standalone tone generator for testing audio outputs.
This runs as a separate process to avoid PortAudio state inheritance.
"""

import sys
import sounddevice as sd
import numpy as np
import signal

def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT gracefully"""
    print(f"Received signal {signum}, exiting", file=sys.stderr, flush=True)
    sys.exit(0)

def generate_tone(device, channel, frequency=1000, volume=0.3, sample_rate=48000, num_channels=None):
    """
    Generate continuous sine wave tone on specified device and channel.
    
    Args:
        device: ALSA device string (e.g., "hw:0,0") or device index (int)
        channel: Output channel number (1-based)
        frequency: Tone frequency in Hz
        volume: Volume level (0.0 to 1.0)
        sample_rate: Sample rate in Hz
    """
    # Set up signal handler for clean shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"Tone generator starting: device={device}, channel={channel}, freq={frequency}Hz", 
          file=sys.stderr, flush=True)
    
    try:
        # Convert device to index if it's a string
        device_index = None
        if isinstance(device, str):
            # Handle "None" string
            if device.lower() == 'none':
                # Use default device (let sounddevice choose)
                device_index = None
                print("Using default audio device", file=sys.stderr, flush=True)
            else:
                # Try to parse as integer first
                try:
                    device_index = int(device)
                except ValueError:
                    # It's a device name, query devices to find it
                    devices = sd.query_devices()
                    print(f"Available devices: {len(devices)}", file=sys.stderr, flush=True)
                    
                    for idx, dev in enumerate(devices):
                        if device in dev['name']:
                            device_index = idx
                            print(f"Found device '{device}' at index {idx}", file=sys.stderr, flush=True)
                            break
                    
                    if device_index is None:
                        # Device name not found, use None (default)
                        print(f"Device '{device}' not found by name, using default device", 
                              file=sys.stderr, flush=True)
                        device_index = None
        else:
            device_index = device
        
        print(f"Using device index {device_index}", file=sys.stderr, flush=True)
        
        # Use provided num_channels or default to 8
        if num_channels is None:
            num_channels = 8
        
        # If device_index is specified, try to query it (but may fail if in use)
        # If None, we'll use PulseAudio default which avoids device conflicts
        if device_index is not None:
            try:
                device_info = sd.query_devices(device_index)
                max_output_channels = device_info['max_output_channels']
                print(f"Device has {max_output_channels} output channels", file=sys.stderr, flush=True)
                
                # Use provided num_channels if given, otherwise use device's max
                if num_channels is None:
                    num_channels = max_output_channels
                    print(f"Using device's max channels: {num_channels}", file=sys.stderr, flush=True)
                else:
                    print(f"Using provided channel count: {num_channels}", file=sys.stderr, flush=True)
                
                if channel > num_channels:
                    print(f"ERROR: Channel {channel} exceeds device channel count {num_channels}", 
                          file=sys.stderr, flush=True)
                    sys.exit(1)
            except Exception as e:
                print(f"Warning: Could not query device info: {e}. Using {num_channels} channels.", 
                      file=sys.stderr, flush=True)
        else:
            print(f"Using default device (PulseAudio) with {num_channels} channels", 
                  file=sys.stderr, flush=True)
        
        # Create output stream
        print(f"Opening device index {device_index} with {num_channels} channels at {sample_rate}Hz",
              file=sys.stderr, flush=True)
        
        # Generate continuous sine wave
        t = 0
        block_size = 256  # Smaller blocksize for lower latency
        dt = 1.0 / sample_rate
        
        def callback(outdata, frames, time_info, status):
            nonlocal t
            if status:
                # Don't print every underflow - it's too noisy
                if 'underflow' not in str(status):
                    print(f"Stream status: {status}", file=sys.stderr, flush=True)
            
            # Generate sine wave for this block - more efficient calculation
            # Use arange with proper length
            sample_indices = np.arange(frames)
            times = (t + sample_indices * dt)
            wave = volume * np.sin(2 * np.pi * frequency * times)
            t += frames * dt
            
            # Create multi-channel output (silence on all channels except target)
            outdata.fill(0)
            if channel <= num_channels:
                # Ensure wave is the right shape and length
                wave_data = wave[:frames] if len(wave) >= frames else np.pad(wave, (0, frames - len(wave)), 'constant')
                outdata[:, channel - 1] = wave_data
            else:
                print(f"ERROR: Channel {channel} > num_channels {num_channels}", file=sys.stderr, flush=True)
            
            # Debug: log first few samples occasionally
            if int(t * sample_rate) % (sample_rate * 2) < frames:  # Every 2 seconds
                print(f"Callback: t={t:.3f}, wave[0]={wave[0]:.3f}, outdata[0,{channel-1}]={outdata[0, channel-1]:.3f}", 
                      file=sys.stderr, flush=True)
        
        # Open stream and keep it running
        # Use the device_index we determined (or None for default)
        try:
            # Use the device_index we determined earlier
            print(f"Opening stream: device={device_index}, channels={num_channels}, rate={sample_rate}, blocksize={block_size}",
                  file=sys.stderr, flush=True)
            stream = sd.OutputStream(device=device_index,  # Use the specified device
                                  channels=num_channels,
                                  samplerate=sample_rate,
                                  blocksize=block_size,
                                  callback=callback,
                                  dtype='float32',
                                  latency='low')
            stream.start()
            print(f"Tone playing on channel {channel}. Press Ctrl+C to stop.",
                  file=sys.stderr, flush=True)
            
            # Run forever until signal
            import time
            while True:
                time.sleep(1)
        except Exception as stream_error:
            # If default device fails, try the specific device
            print(f"Default device failed: {stream_error}, trying device {device_index}",
                  file=sys.stderr, flush=True)
            stream = sd.OutputStream(device=device_index,
                                    channels=num_channels,
                                    samplerate=sample_rate,
                                    blocksize=block_size,
                                    callback=callback)
            stream.start()
            print(f"Tone playing on channel {channel} (device {device_index}). Press Ctrl+C to stop.",
                  file=sys.stderr, flush=True)
            import time
            while True:
                time.sleep(1)
                
    except Exception as e:
        print(f"Tone generator error: {e}", file=sys.stderr, flush=True)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: tone_generator.py <device> <channel> [frequency] [volume] [num_channels]", 
              file=sys.stderr)
        sys.exit(1)
    
    device = sys.argv[1]
    channel = int(sys.argv[2])
    frequency = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
    volume = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    num_channels_override = int(sys.argv[5]) if len(sys.argv) > 5 else None
    
    # Call generate_tone with num_channels if provided
    generate_tone(device, channel, frequency, volume, num_channels=num_channels_override)
