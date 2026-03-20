"""S-DSP emulator — ported from the reference C codegen implementation.

Architecture matches the reference exactly:
- 19-element voice buffer (0-2 = prev block tail, 3-18 = current block)
- Pitch counter with 0x1000 threshold
- Immediate KON handling in dsp_write (no latching/delay)
- Per-voice rate counters for envelope
- Reference Gaussian table
- BRR filter coefficients from reference C
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Gaussian interpolation table (512 entries, from DSP ROM) — reference version
# ---------------------------------------------------------------------------
GAUSS = (
       0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,
       1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   1,   2,   2,   2,   2,   2,
       2,   2,   3,   3,   3,   3,   3,   4,   4,   4,   4,   4,   5,   5,   5,   5,
       6,   6,   6,   6,   7,   7,   7,   8,   8,   8,   9,   9,   9,  10,  10,  10,
      11,  11,  11,  12,  12,  13,  13,  14,  14,  15,  15,  15,  16,  16,  17,  17,
      18,  19,  19,  20,  20,  21,  21,  22,  23,  23,  24,  24,  25,  26,  27,  27,
      28,  29,  29,  30,  31,  32,  32,  33,  34,  35,  36,  36,  37,  38,  39,  40,
      41,  42,  43,  44,  45,  46,  47,  48,  49,  50,  51,  52,  53,  54,  55,  56,
      58,  59,  60,  61,  62,  64,  65,  66,  67,  69,  70,  71,  73,  74,  76,  77,
      78,  80,  81,  83,  84,  86,  87,  89,  90,  92,  94,  95,  97,  99, 100, 102,
     104, 106, 107, 109, 111, 113, 115, 117, 118, 120, 122, 124, 126, 128, 130, 132,
     134, 137, 139, 141, 143, 145, 147, 150, 152, 154, 156, 159, 161, 163, 166, 168,
     171, 173, 175, 178, 180, 183, 186, 188, 191, 193, 196, 199, 201, 204, 207, 210,
     212, 215, 218, 221, 224, 227, 230, 233, 236, 239, 242, 245, 248, 251, 254, 257,
     260, 263, 267, 270, 273, 276, 280, 283, 286, 290, 293, 297, 300, 304, 307, 311,
     314, 318, 321, 325, 328, 332, 336, 339, 343, 347, 351, 354, 358, 362, 366, 370,
     374, 378, 381, 385, 389, 393, 397, 401, 405, 410, 414, 418, 422, 426, 430, 434,
     439, 443, 447, 451, 456, 460, 464, 469, 473, 477, 482, 486, 491, 495, 499, 504,
     508, 513, 517, 522, 527, 531, 536, 540, 545, 550, 554, 559, 563, 568, 573, 577,
     582, 587, 592, 596, 601, 606, 611, 615, 620, 625, 630, 635, 640, 644, 649, 654,
     659, 664, 669, 674, 678, 683, 688, 693, 698, 703, 708, 713, 718, 723, 728, 732,
     737, 742, 747, 752, 757, 762, 767, 772, 777, 782, 787, 792, 797, 802, 806, 811,
     816, 821, 826, 831, 836, 841, 846, 851, 855, 860, 865, 870, 875, 880, 884, 889,
     894, 899, 904, 908, 913, 918, 923, 927, 932, 937, 941, 946, 951, 955, 960, 965,
     969, 974, 978, 983, 988, 992, 997,1001,1005,1010,1014,1019,1023,1027,1032,1036,
    1040,1045,1049,1053,1057,1061,1066,1070,1074,1078,1082,1086,1090,1094,1098,1102,
    1106,1109,1113,1117,1121,1125,1128,1132,1136,1139,1143,1146,1150,1153,1157,1160,
    1164,1167,1170,1174,1177,1180,1183,1186,1190,1193,1196,1199,1202,1205,1207,1210,
    1213,1216,1219,1221,1224,1227,1229,1232,1234,1237,1239,1241,1244,1246,1248,1251,
    1253,1255,1257,1259,1261,1263,1265,1267,1269,1270,1272,1274,1275,1277,1279,1280,
    1282,1283,1284,1286,1287,1288,1290,1291,1292,1293,1294,1295,1296,1297,1297,1298,
    1299,1300,1300,1301,1302,1302,1303,1303,1303,1304,1304,1304,1304,1305,1305,1305,
)

# ---------------------------------------------------------------------------
# Rate period table: maps rate index (0-31) to sample period.
# Rate 0 = never step.  Used by noise LFSR and envelope counters.
# ---------------------------------------------------------------------------
RATE_TABLE = (
    0, 2048, 1536, 1280, 1024, 768, 640, 512,
    384,  320,  256,  192,  160, 128,  96,  80,
     64,   48,   40,   32,   24,  20,  16,  12,
     10,    8,    6,    5,    4,   3,   2,   1,
)


def _clamp16(v: int) -> int:
    if v > 32767:
        return 32767
    if v < -32768:
        return -32768
    return v


def _sign8(v: int) -> int:
    """Interpret a byte as signed int8."""
    return v - 256 if v & 0x80 else v


def _to_s16(v: int) -> int:
    """Cast to signed 16-bit (mimics C int16_t truncation)."""
    v &= 0xFFFF
    return v - 0x10000 if v >= 0x8000 else v


# ---------------------------------------------------------------------------
# DSP class
# ---------------------------------------------------------------------------
class DSP:
    """S-DSP emulator matching the reference C codegen implementation."""

    def __init__(self, ram: bytearray) -> None:
        self.ram = ram
        self.regs = bytearray(128)

        # Per-voice state (flat arrays matching reference struct)
        self.voice_brr_addr = [0] * 8
        self.voice_brr_offset = [0] * 8          # sample offset within BRR block (0-15)
        self.voice_buf = [[0] * 19 for _ in range(8)]  # 19-element buffer per voice
        self.voice_brr_old = [0] * 8              # BRR filter: previous sample
        self.voice_brr_older = [0] * 8            # BRR filter: sample before previous
        self.voice_pitch_counter = [0] * 8        # pitch counter (12.4 fixed-point)
        self.voice_env_level = [0] * 8            # envelope level (0-0x7FF)
        self.voice_env_mode = [0] * 8             # 0=attack, 1=decay, 2=sustain, 3=release
        self.voice_env_counter = [0] * 8          # per-voice envelope rate counter
        self.voice_active = [0] * 8               # voice currently active
        self.voice_end_flag = [0] * 8             # BRR end flag detected

        # Noise
        self.noise_lfsr: int = 0x4000
        self.noise_counter: int = 0

        # Echo
        self.echo_pos: int = 0
        self.fir_buf_l = [0] * 8
        self.fir_buf_r = [0] * 8
        self.fir_pos: int = 0

        # DSP sample generation cycle accumulator
        self.sample_counter: int = 0

        # Debug
        self.debug_mute = [0] * 8

    # ===================================================================
    # DSP register write — called by CPU when writing to $F3
    # Handles KON, KOFF, FLG immediately (no latching).
    # ===================================================================
    def dsp_write(self, addr: int, val: int) -> None:
        addr &= 0x7F
        val &= 0xFF

        # ENDX (0x7C): any write clears all bits
        if addr == 0x7C:
            self.regs[0x7C] = 0
            return

        self.regs[addr] = val

        # Handle KON (0x4C) — key on
        if addr == 0x4C:
            # Soft reset (FLG bit 7) prevents key-on
            if self.regs[0x6C] & 0x80:
                return
            ram = self.ram
            for v in range(8):
                if val & (1 << v):
                    # Key on voice v: set up BRR source from directory
                    srcn = self.regs[(v << 4) | 0x04]
                    dir_base = self.regs[0x5D] << 8
                    entry_addr = (dir_base + srcn * 4) & 0xFFFF
                    self.voice_brr_addr[v] = ram[entry_addr] | (ram[(entry_addr + 1) & 0xFFFF] << 8)
                    self.voice_brr_offset[v] = 0
                    self.voice_brr_old[v] = 0
                    self.voice_brr_older[v] = 0
                    self.voice_pitch_counter[v] = 0
                    self.voice_env_level[v] = 0
                    self.voice_env_mode[v] = 0   # Attack
                    self.voice_env_counter[v] = 0
                    self.voice_active[v] = 1
                    self.voice_end_flag[v] = 0
                    # Clear interpolation context
                    buf = self.voice_buf[v]
                    buf[0] = 0
                    buf[1] = 0
                    buf[2] = 0
                    # Clear ENDX bit for this voice
                    self.regs[0x7C] &= ~(1 << v) & 0xFF
                    # Decode first BRR block
                    self._brr_decode_block(v)

        # Handle KOFF (0x5C) — key off
        elif addr == 0x5C:
            for v in range(8):
                if val & (1 << v):
                    self.voice_env_mode[v] = 3   # Release

        # Handle FLG (0x6C) — flags
        elif addr == 0x6C:
            if val & 0x80:
                # Soft reset: force all voices to release with zero envelope
                for v in range(8):
                    self.voice_env_mode[v] = 3   # Release
                    self.voice_env_level[v] = 0

    # ===================================================================
    # BRR decoder — reference-accurate filter coefficients
    # ===================================================================
    def _brr_decode_block(self, voice: int) -> None:
        """Decode one 9-byte BRR block into voice_buf[voice][3..18]."""
        ram = self.ram
        addr = self.voice_brr_addr[voice] & 0xFFFF
        header = ram[addr]
        range_shift = (header >> 4) & 0x0F
        filt = (header >> 2) & 0x03

        old = self.voice_brr_old[voice]
        older = self.voice_brr_older[voice]
        buf = self.voice_buf[voice]

        for i in range(8):
            byte = ram[(addr + 1 + i) & 0xFFFF]

            for nibble in range(2):
                if nibble == 0:
                    s = (byte >> 4) & 0x0F
                else:
                    s = byte & 0x0F

                # Sign-extend from 4 bits
                if s >= 8:
                    s -= 16

                # Apply range shift
                if range_shift <= 12:
                    s = (s << range_shift) >> 1
                else:
                    s = -2048 if s < 0 else 0

                # Apply filter — exact reference C coefficients
                if filt == 1:
                    s += old + (-old >> 4)
                elif filt == 2:
                    s += (old << 1) + ((-3 * old) >> 5) - older + (older >> 4)
                elif filt == 3:
                    s += (old << 1) + ((-13 * old) >> 6) - older + ((3 * older) >> 4)

                # Clamp to 16-bit signed
                if s > 32767:
                    s = 32767
                if s < -32768:
                    s = -32768

                # Clip to 15-bit (hardware behavior)
                s = _to_s16(s << 1) >> 1

                older = old
                old = s

                # Store at indices 3-18 in the buffer
                buf[i * 2 + nibble + 3] = s

        self.voice_brr_old[voice] = old
        self.voice_brr_older[voice] = older
        self.voice_brr_offset[voice] = 0

    # ===================================================================
    # Generate one stereo sample — full reference pipeline
    # ===================================================================
    def generate_sample(self) -> tuple[int, int]:
        regs = self.regs
        ram = self.ram

        out_l = 0
        out_r = 0
        echo_in_l = 0
        echo_in_r = 0

        flg = regs[0x6C]
        non = regs[0x3D]    # Noise enable register
        eon = regs[0x4D]    # Echo enable register
        pmon = regs[0x2D]   # Pitch modulation register
        prev_output = 0     # Previous voice output for PMON

        # --- Step noise LFSR at rate from FLG bits 0-4 ---
        noise_rate = flg & 0x1F
        if noise_rate > 0:
            period = RATE_TABLE[noise_rate]
            self.noise_counter += 1
            if self.noise_counter >= period:
                self.noise_counter = 0
                # 15-bit LFSR: feedback = bit0 XOR bit1, shift right, insert at bit 14
                lfsr = self.noise_lfsr & 0x7FFF
                feedback = (lfsr ^ (lfsr >> 1)) & 1
                self.noise_lfsr = _to_s16((lfsr >> 1) | (feedback << 14))

        for v in range(8):
            if not self.voice_active[v]:
                prev_output = 0
                continue
            if self.debug_mute[v]:
                prev_output = 0
                continue

            # --- Get sample: noise or BRR with Gaussian interpolation ---
            if non & (1 << v):
                # Noise voice: use LFSR output, sign-extended from 15 bits
                sample = _to_s16(self.noise_lfsr << 1) >> 1
            else:
                # 4-point Gaussian interpolation from BRR sample buffer
                off = self.voice_brr_offset[v]
                gi = (self.voice_pitch_counter[v] >> 4) & 0xFF
                buf = self.voice_buf[v]
                s0 = buf[off]
                s1 = buf[off + 1]
                s2 = buf[off + 2]
                s3 = buf[off + 3]

                out_g = (GAUSS[255 - gi] * s0) >> 11
                out_g += (GAUSS[511 - gi] * s1) >> 11
                out_g += (GAUSS[256 + gi] * s2) >> 11
                out_g += (GAUSS[gi] * s3) >> 11

                if out_g > 32767:
                    out_g = 32767
                if out_g < -32768:
                    out_g = -32768
                sample = out_g & ~1  # Clear LSB (hardware behavior)

            # --- ADSR / GAIN Envelope ---
            env = self.voice_env_level[v]
            adsr1 = regs[(v << 4) | 0x05]
            adsr2 = regs[(v << 4) | 0x06]
            gain_reg = regs[(v << 4) | 0x07]

            if self.voice_env_mode[v] == 3:
                # Release: always -8 per sample
                env -= 8
                if env <= 0:
                    env = 0
                    self.voice_active[v] = 0

            elif adsr1 & 0x80:
                # --- ADSR mode ---
                mode = self.voice_env_mode[v]
                if mode == 0:
                    # Attack
                    rate_idx = ((adsr1 & 0x0F) << 1) + 1
                    period = RATE_TABLE[rate_idx & 0x1F]
                    if period > 0:
                        self.voice_env_counter[v] += 1
                        if self.voice_env_counter[v] >= period:
                            self.voice_env_counter[v] = 0
                            env += 1024 if rate_idx == 31 else 32
                            if env > 0x7FF:
                                env = 0x7FF
                    if env >= 0x7FF:
                        env = 0x7FF
                        self.voice_env_mode[v] = 1   # -> Decay
                        self.voice_env_counter[v] = 0

                elif mode == 1:
                    # Decay
                    rate_idx = (((adsr1 >> 4) & 0x07) << 1) + 16
                    period = RATE_TABLE[rate_idx & 0x1F]
                    if period > 0:
                        self.voice_env_counter[v] += 1
                        if self.voice_env_counter[v] >= period:
                            self.voice_env_counter[v] = 0
                            env -= ((env - 1) >> 8) + 1
                            if env < 0:
                                env = 0
                    sl = (adsr2 >> 5) & 0x07
                    sl_threshold = (sl + 1) << 8
                    if env <= sl_threshold:
                        self.voice_env_mode[v] = 2   # -> Sustain
                        self.voice_env_counter[v] = 0

                elif mode == 2:
                    # Sustain
                    rate_idx = adsr2 & 0x1F
                    if rate_idx > 0:
                        period = RATE_TABLE[rate_idx]
                        self.voice_env_counter[v] += 1
                        if self.voice_env_counter[v] >= period:
                            self.voice_env_counter[v] = 0
                            env -= ((env - 1) >> 8) + 1
                            if env < 0:
                                env = 0

            else:
                # --- GAIN mode ---
                if not (gain_reg & 0x80):
                    # Direct mode: set level immediately
                    env = (gain_reg & 0x7F) << 4
                else:
                    # Variable rate mode
                    gain_mode = (gain_reg >> 5) & 0x03
                    gain_rate = gain_reg & 0x1F
                    if gain_rate > 0:
                        period = RATE_TABLE[gain_rate]
                        self.voice_env_counter[v] += 1
                        if self.voice_env_counter[v] >= period:
                            self.voice_env_counter[v] = 0
                            if gain_mode == 0:
                                # Linear decrease
                                env -= 32
                            elif gain_mode == 1:
                                # Exponential decrease
                                env -= ((env - 1) >> 8) + 1
                            elif gain_mode == 2:
                                # Linear increase
                                env += 32
                            elif gain_mode == 3:
                                # Bent-line increase
                                env += 32 if env < 0x600 else 8
                    if env > 0x7FF:
                        env = 0x7FF
                    if env < 0:
                        env = 0

            self.voice_env_level[v] = env

            # Apply envelope to sample
            output = (sample * env) >> 11

            # Apply per-voice volume (signed 8-bit)
            vol_l = _sign8(regs[(v << 4) | 0x00])
            vol_r = _sign8(regs[(v << 4) | 0x01])
            voice_l = (output * vol_l) >> 7
            voice_r = (output * vol_r) >> 7
            out_l += voice_l
            out_r += voice_r

            # Accumulate echo input for voices with EON bit set
            if eon & (1 << v):
                echo_in_l += voice_l
                echo_in_r += voice_r

            # --- Advance pitch counter (with pitch modulation) ---
            pitch = regs[(v << 4) | 0x02] | ((regs[(v << 4) | 0x03] & 0x3F) << 8)
            if (pmon & (1 << v)) and v > 0:
                pitch += ((pitch * prev_output) >> 10) & ~1
                if pitch < 0:
                    pitch = 0
                if pitch > 0x3FFF:
                    pitch = 0x3FFF

            prev_output = output  # Save for next voice's pitch modulation

            self.voice_pitch_counter[v] += pitch

            # --- Advance BRR sample position ---
            while self.voice_pitch_counter[v] >= 0x1000:
                self.voice_pitch_counter[v] -= 0x1000
                self.voice_brr_offset[v] += 1

                if self.voice_brr_offset[v] >= 16:
                    # Advance to next BRR block
                    brr_addr = self.voice_brr_addr[v]
                    header = ram[brr_addr & 0xFFFF]
                    end_flag = header & 1
                    loop_flag = (header >> 1) & 1

                    if end_flag:
                        # Set ENDX bit for this voice
                        regs[0x7C] |= (1 << v)
                        self.voice_end_flag[v] = 1

                        if loop_flag:
                            # Loop: get loop address from directory
                            srcn = regs[(v << 4) | 0x04]
                            dir_base = regs[0x5D] << 8
                            entry = (dir_base + srcn * 4) & 0xFFFF
                            self.voice_brr_addr[v] = ram[entry + 2] | (ram[(entry + 3) & 0xFFFF] << 8)
                        else:
                            self.voice_active[v] = 0
                            self.voice_env_level[v] = 0
                            break
                    else:
                        self.voice_brr_addr[v] = (brr_addr + 9) & 0xFFFF

                    # Save last 3 samples as interpolation context for next block
                    buf = self.voice_buf[v]
                    buf[0] = buf[16]
                    buf[1] = buf[17]
                    buf[2] = buf[18]
                    self._brr_decode_block(v)

        # --- Echo Buffer + FIR Filter ---

        # Read echo sample from SPC700 RAM
        esa = regs[0x6D] << 8
        edl = regs[0x7D] & 0x0F
        echo_len = edl * 2048 if edl else 4
        echo_addr = (esa + self.echo_pos) & 0xFFFF

        echo_l_ram = ram[echo_addr] | (ram[(echo_addr + 1) & 0xFFFF] << 8)
        if echo_l_ram >= 0x8000:
            echo_l_ram -= 0x10000
        echo_r_ram = ram[(echo_addr + 2) & 0xFFFF] | (ram[(echo_addr + 3) & 0xFFFF] << 8)
        if echo_r_ram >= 0x8000:
            echo_r_ram -= 0x10000

        # Push into FIR history ring buffer (>> 1 per hardware)
        fpos = self.fir_pos
        self.fir_buf_l[fpos] = echo_l_ram >> 1
        self.fir_buf_r[fpos] = echo_r_ram >> 1
        # Advance fir_pos BEFORE the FIR loop (reference order)
        fpos = (fpos + 1) & 7
        self.fir_pos = fpos

        # 8-tap FIR filter
        fir_l = 0
        fir_r = 0
        fbl = self.fir_buf_l
        fbr = self.fir_buf_r
        for t in range(8):
            idx = (fpos + t) & 7
            coeff = _sign8(regs[t * 0x10 + 0x0F])
            fir_l += fbl[idx] * coeff
            fir_r += fbr[idx] * coeff

        fir_l >>= 6
        fir_r >>= 6
        fir_l = _clamp16(fir_l)
        fir_r = _clamp16(fir_r)
        fir_l &= ~1
        fir_r &= ~1

        # Final output = dry * master_vol + fir * echo_vol
        mvol_l = _sign8(regs[0x0C])
        mvol_r = _sign8(regs[0x1C])
        evol_l = _sign8(regs[0x2C])
        evol_r = _sign8(regs[0x3C])
        out_l = ((out_l * mvol_l) >> 7) + ((fir_l * evol_l) >> 7)
        out_r = ((out_r * mvol_r) >> 7) + ((fir_r * evol_r) >> 7)

        # Echo write: echo_in + fir * feedback
        efb = _sign8(regs[0x0D])
        ew_l = _clamp16(echo_in_l + ((fir_l * efb) >> 7))
        ew_r = _clamp16(echo_in_r + ((fir_r * efb) >> 7))

        # Write to echo buffer (unless FLG bit 5 disables or echo not configured)
        if not (flg & 0x20) and (esa | edl):
            ram[echo_addr] = ew_l & 0xFF
            ram[(echo_addr + 1) & 0xFFFF] = (ew_l >> 8) & 0xFF
            ram[(echo_addr + 2) & 0xFFFF] = ew_r & 0xFF
            ram[(echo_addr + 3) & 0xFFFF] = (ew_r >> 8) & 0xFF

        # Advance echo buffer position
        self.echo_pos += 4
        if self.echo_pos >= echo_len:
            self.echo_pos = 0

        # FLG mute (bit 6): silence all output
        if flg & 0x40:
            out_l = 0
            out_r = 0

        # Clamp to 16-bit
        out_l = _clamp16(out_l)
        out_r = _clamp16(out_r)

        return out_l, out_r
