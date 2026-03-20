"""SPC700 emulator — loads .spc files, runs CPU+DSP, renders to WAV."""

from __future__ import annotations

import argparse
import struct
import wave
from pathlib import Path

from .spc700_cpu import SPC700
from .spc700_dsp import DSP

# SPC file format constants
SPC_HEADER_MAGIC = b"SNES-SPC700 Sound File Data v0.30"
SPC_HEADER_SIZE = 0x100
SPC_RAM_OFFSET = 0x100
SPC_RAM_SIZE = 0x10000
SPC_DSP_OFFSET = 0x10100
SPC_DSP_SIZE = 128
SPC_IPL_OFFSET = 0x101C0

# Offsets for registers within the header
SPC_PC_OFFSET = 0x25
SPC_A_OFFSET = 0x27
SPC_X_OFFSET = 0x28
SPC_Y_OFFSET = 0x29
SPC_PSW_OFFSET = 0x2A
SPC_SP_OFFSET = 0x2B

# CPU clock and sample rate
CPU_CLOCK = 1024000  # 1.024 MHz
SAMPLE_RATE = 32000
CYCLES_PER_SAMPLE = CPU_CLOCK // SAMPLE_RATE  # 32 cycles


def load_spc(path: str) -> tuple[SPC700, DSP]:
    """Load an .spc file and return initialized CPU and DSP."""
    data = Path(path).read_bytes()

    if len(data) < SPC_DSP_OFFSET + SPC_DSP_SIZE:
        raise ValueError(f"File too small to be a valid SPC: {len(data)} bytes")

    # Verify magic (allow partial match — some rips have variant headers)
    header = data[:33]
    if b"SNES-SPC700" not in header and b"spc" not in header.lower():
        # Be lenient — try to load anyway
        pass

    # Create CPU
    cpu = SPC700()

    # Load 64KB RAM
    ram_data = data[SPC_RAM_OFFSET:SPC_RAM_OFFSET + SPC_RAM_SIZE]
    if len(ram_data) < SPC_RAM_SIZE:
        ram_data = ram_data + bytes(SPC_RAM_SIZE - len(ram_data))
    cpu.ram[:] = ram_data

    # Load CPU registers
    cpu.pc = struct.unpack_from("<H", data, SPC_PC_OFFSET)[0]
    cpu.a = data[SPC_A_OFFSET]
    cpu.x = data[SPC_X_OFFSET]
    cpu.y = data[SPC_Y_OFFSET]
    cpu.set_psw(data[SPC_PSW_OFFSET])
    cpu.sp = data[SPC_SP_OFFSET]

    # Create DSP with shared RAM
    dsp = DSP(cpu.ram)

    # Load DSP registers — first load raw bytes for read-back, then
    # use dsp_write for KON/KOFF/FLG handling (dsp_write reads other
    # registers like SRCN and DIR, so raw regs must be populated first).
    dsp_data = data[SPC_DSP_OFFSET:SPC_DSP_OFFSET + SPC_DSP_SIZE]
    dsp.regs[:len(dsp_data)] = dsp_data[:128]

    # Wire CPU <-> DSP
    cpu.dsp = dsp

    # Now process KON through dsp_write so voices get properly keyed on
    initial_kon = dsp.regs[0x4C]
    if initial_kon:
        dsp.dsp_write(0x4C, initial_kon)

    # Disable IPL ROM (games have already loaded their program into RAM)
    cpu.ipl_rom_enabled = False

    # Set up timer dividers from RAM I/O area
    cpu.timer_div[0] = cpu.ram[0xFA]
    cpu.timer_div[1] = cpu.ram[0xFB]
    cpu.timer_div[2] = cpu.ram[0xFC]

    # Set up timer enables from CONTROL register
    ctrl = cpu.ram[0xF1]
    cpu.timer_en[0] = bool(ctrl & 0x01)
    cpu.timer_en[1] = bool(ctrl & 0x02)
    cpu.timer_en[2] = bool(ctrl & 0x04)
    cpu.ipl_rom_enabled = bool(ctrl & 0x80)

    print(f"Loaded SPC: PC=${cpu.pc:04X} A=${cpu.a:02X} X=${cpu.x:02X} "
          f"Y=${cpu.y:02X} SP=${cpu.sp:02X} PSW=${cpu.get_psw():02X}")

    return cpu, dsp


def render_wav(cpu: SPC700, dsp: DSP, output_path: str,
               duration: float = 30.0, progress: bool = True) -> None:
    """Run the emulator and render audio to a WAV file."""
    total_samples = int(SAMPLE_RATE * duration)

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)

        buf = bytearray()
        flush_interval = SAMPLE_RATE  # flush every second

        for sample_idx in range(total_samples):
            # Run CPU for the cycles corresponding to one DSP sample
            target = (sample_idx + 1) * CYCLES_PER_SAMPLE
            cpu.run_cycles(target)

            # Generate one DSP sample
            left, right = dsp.generate_sample()

            # Pack as 16-bit signed little-endian
            buf += struct.pack("<hh", left, right)

            if len(buf) >= flush_interval * 4:
                wf.writeframes(buf)
                buf = bytearray()

                if progress:
                    elapsed = (sample_idx + 1) / SAMPLE_RATE
                    pct = (sample_idx + 1) / total_samples * 100
                    print(f"\r  Rendering: {elapsed:.1f}s / {duration:.1f}s ({pct:.0f}%)",
                          end="", flush=True)

        if buf:
            wf.writeframes(buf)

    if progress:
        print(f"\r  Rendering: {duration:.1f}s / {duration:.1f}s (100%)")

    print(f"Wrote {output_path} ({total_samples} samples, {duration:.1f}s, "
          f"stereo 16-bit {SAMPLE_RATE}Hz)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SPC700 SNES sound chip emulator — renders .spc files to WAV"
    )
    parser.add_argument("input", help="Input .spc file")
    parser.add_argument("-o", "--output", help="Output .wav file (default: <input>.wav)")
    parser.add_argument("-d", "--duration", type=float, default=30.0,
                        help="Duration in seconds (default: 30)")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Suppress progress output")
    args = parser.parse_args()

    output = args.output
    if not output:
        output = Path(args.input).stem + ".wav"

    cpu, dsp = load_spc(args.input)
    render_wav(cpu, dsp, output, duration=args.duration, progress=not args.quiet)


if __name__ == "__main__":
    main()
