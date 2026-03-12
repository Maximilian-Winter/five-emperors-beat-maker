"""SPC700 CPU interpreter — all 256 opcodes.

Ported from the reference implementation (spc700/ codegen framework).
All opcodes, flag computations, and addressing modes match the reference exactly.
"""

from __future__ import annotations


def _s8(v: int) -> int:
    """Interpret an 8-bit value as signed (-128..127)."""
    return v - 256 if v & 0x80 else v


class SPC700:
    """SPC700 8-bit CPU emulator."""

    def __init__(self) -> None:
        # Registers
        self.a: int = 0
        self.x: int = 0
        self.y: int = 0
        self.sp: int = 0xFF
        self.pc: int = 0xFFC0
        # PSW flags stored individually for speed
        self.flag_n: int = 0
        self.flag_v: int = 0
        self.flag_p: int = 0
        self.flag_b: int = 0
        self.flag_h: int = 0
        self.flag_i: int = 0
        self.flag_z: int = 1  # Z=1 means result==0
        self.flag_c: int = 0

        # 64 KB RAM
        self.ram = bytearray(0x10000)

        # I/O ports written by main CPU (read via $F4-$F7)
        self.in_ports = [0, 0, 0, 0]
        # I/O ports written by SPC700 (read by main CPU)
        self.out_ports = [0, 0, 0, 0]

        # Timers
        self.timer_div = [0, 0, 0]   # T0DIV..T2DIV
        self.timer_cnt = [0, 0, 0]   # internal counter (cycle accumulator)
        self.timer_tick = [0, 0, 0]  # internal tick counter
        self.timer_out = [0, 0, 0]   # T0OUT..T2OUT (4-bit)
        self.timer_en = [False, False, False]

        # DSP interface (set externally)
        self.dsp = None
        self.dsp_addr: int = 0

        # IPL ROM enable
        self.ipl_rom_enabled: bool = True
        self.ipl_rom = bytearray(64)

        # State
        self.halted: bool = False
        self.cycles: int = 0

        self._build_opcode_table()

    # ------------------------------------------------------------------ PSW
    def get_psw(self) -> int:
        return ((self.flag_n & 1) << 7 |
                (self.flag_v & 1) << 6 |
                (self.flag_p & 1) << 5 |
                (self.flag_b & 1) << 4 |
                (self.flag_h & 1) << 3 |
                (self.flag_i & 1) << 2 |
                (self.flag_z & 1) << 1 |
                (self.flag_c & 1))

    def set_psw(self, v: int) -> None:
        self.flag_n = (v >> 7) & 1
        self.flag_v = (v >> 6) & 1
        self.flag_p = (v >> 5) & 1
        self.flag_b = (v >> 4) & 1
        self.flag_h = (v >> 3) & 1
        self.flag_i = (v >> 2) & 1
        self.flag_z = (v >> 1) & 1
        self.flag_c = v & 1

    # ----------------------------------------------------------- Memory I/O
    def _dp(self) -> int:
        """Direct page base: 0x0100 if P flag set, else 0x0000."""
        return 0x0100 if self.flag_p else 0x0000

    def read(self, addr: int) -> int:
        addr &= 0xFFFF
        if 0x00F0 <= addr <= 0x00FF:
            return self._read_io(addr)
        if addr >= 0xFFC0 and self.ipl_rom_enabled:
            return self.ipl_rom[addr - 0xFFC0]
        return self.ram[addr]

    def write(self, addr: int, val: int) -> None:
        addr &= 0xFFFF
        val &= 0xFF
        if 0x00F0 <= addr <= 0x00FF:
            self._write_io(addr, val)
            return
        self.ram[addr] = val

    def _read_io(self, addr: int) -> int:
        r = addr & 0xFF
        if r == 0xF0:
            return 0  # TEST register
        if r == 0xF1:
            return 0  # CONTROL (write-only)
        if r == 0xF2:
            return self.dsp_addr
        if r == 0xF3:
            if self.dsp and (self.dsp_addr & 0x7F) < 128:
                return self.dsp.regs[self.dsp_addr & 0x7F]
            return 0
        if 0xF4 <= r <= 0xF7:
            return self.in_ports[r - 0xF4]
        if r == 0xF8:
            return self.ram[0xF8]
        if r == 0xF9:
            return self.ram[0xF9]
        if 0xFA <= r <= 0xFC:
            return 0  # Timer dividers are write-only
        if r == 0xFD:
            v = self.timer_out[0] & 0x0F
            self.timer_out[0] = 0
            return v
        if r == 0xFE:
            v = self.timer_out[1] & 0x0F
            self.timer_out[1] = 0
            return v
        if r == 0xFF:
            v = self.timer_out[2] & 0x0F
            self.timer_out[2] = 0
            return v
        return self.ram[addr]

    def _write_io(self, addr: int, val: int) -> None:
        r = addr & 0xFF
        if r == 0xF0:
            return  # TEST
        if r == 0xF1:  # CONTROL
            # Timer enable -- reset counters when newly enabled
            for i in range(3):
                new_en = bool(val & (1 << i))
                if new_en and not self.timer_en[i]:
                    self.timer_cnt[i] = 0
                    self.timer_tick[i] = 0
                    self.timer_out[i] = 0
                self.timer_en[i] = new_en
            # Port clear
            if val & 0x10:
                self.in_ports[0] = 0
                self.in_ports[1] = 0
            if val & 0x20:
                self.in_ports[2] = 0
                self.in_ports[3] = 0
            self.ipl_rom_enabled = bool(val & 0x80)
            return
        if r == 0xF2:
            self.dsp_addr = val
            return
        if r == 0xF3:
            if self.dsp:
                self.dsp.dsp_write(self.dsp_addr & 0x7F, val)
            return
        if 0xF4 <= r <= 0xF7:
            self.out_ports[r - 0xF4] = val
            self.ram[addr] = val
            return
        if r == 0xF8:
            self.ram[0xF8] = val
            return
        if r == 0xF9:
            self.ram[0xF9] = val
            return
        if r == 0xFA:
            self.timer_div[0] = val
            return
        if r == 0xFB:
            self.timer_div[1] = val
            return
        if r == 0xFC:
            self.timer_div[2] = val
            return
        # FD-FF are read-only timer outputs

    # -------------------------------------------------------------- Timers
    def _tick_timers(self, elapsed: int) -> None:
        # Timer 0 & 1: tick every 128 CPU cycles (8 kHz)
        for i in range(2):
            if self.timer_en[i]:
                self.timer_cnt[i] += elapsed
                while self.timer_cnt[i] >= 128:
                    self.timer_cnt[i] -= 128
                    self.timer_tick[i] += 1
                    div = self.timer_div[i] if self.timer_div[i] else 256
                    if self.timer_tick[i] >= div:
                        self.timer_tick[i] = 0
                        self.timer_out[i] = (self.timer_out[i] + 1) & 0x0F

        # Timer 2: tick every 16 CPU cycles (64 kHz)
        if self.timer_en[2]:
            self.timer_cnt[2] += elapsed
            while self.timer_cnt[2] >= 16:
                self.timer_cnt[2] -= 16
                self.timer_tick[2] += 1
                div = self.timer_div[2] if self.timer_div[2] else 256
                if self.timer_tick[2] >= div:
                    self.timer_tick[2] = 0
                    self.timer_out[2] = (self.timer_out[2] + 1) & 0x0F

    # -------------------------------------------------------- Fetch helpers
    def _fetch(self) -> int:
        v = self.read(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return v

    def _fetch16(self) -> int:
        lo = self._fetch()
        hi = self._fetch()
        return lo | (hi << 8)

    # ----------------------------------------------------- Flag helpers
    def _set_nz(self, val: int) -> None:
        """Set N and Z flags from an 8-bit value."""
        val &= 0xFF
        self.flag_n = 1 if val & 0x80 else 0
        self.flag_z = 1 if val == 0 else 0

    def _set_nz16(self, val: int) -> None:
        """Set N and Z flags from a 16-bit value."""
        val &= 0xFFFF
        self.flag_n = 1 if val & 0x8000 else 0
        self.flag_z = 1 if val == 0 else 0

    # -------------------------------------------------- Stack helpers
    def _push(self, val: int) -> None:
        self.ram[0x0100 + self.sp] = val & 0xFF
        self.sp = (self.sp - 1) & 0xFF

    def _pop(self) -> int:
        self.sp = (self.sp + 1) & 0xFF
        return self.ram[0x0100 + self.sp]

    def _push16(self, val: int) -> None:
        self._push((val >> 8) & 0xFF)
        self._push(val & 0xFF)

    def _pop16(self) -> int:
        lo = self._pop()
        hi = self._pop()
        return lo | (hi << 8)

    # -------------------------------------------- Addressing helpers
    def _dp_addr(self, offset: int) -> int:
        """Direct page address from 8-bit offset."""
        return (self._dp() + offset) & 0xFFFF

    # -------------------------------------------- ALU core operations
    def _adc(self, a: int, val: int) -> int:
        """ADC: a + val + C -> result. Sets H, V, C, N, Z. Returns 8-bit result."""
        result = a + val + self.flag_c
        self.flag_h = 1 if ((a & 0xF) + (val & 0xF) + self.flag_c) > 0xF else 0
        self.flag_v = 1 if (~(a ^ val) & (a ^ result) & 0x80) else 0
        self.flag_c = 1 if result > 0xFF else 0
        result &= 0xFF
        self._set_nz(result)
        return result

    def _sbc(self, a: int, val: int) -> int:
        """SBC: a - val - !C -> result. Sets H, V, C, N, Z. Returns 8-bit result."""
        borrow = 0 if self.flag_c else 1
        result = a - val - borrow
        self.flag_h = 1 if ((a & 0xF) - (val & 0xF) - borrow) >= 0 else 0
        self.flag_v = 1 if ((a ^ val) & (a ^ result) & 0x80) else 0
        self.flag_c = 1 if (result & 0xFFFF) <= 0xFF else 0
        result &= 0xFF
        self._set_nz(result)
        return result

    def _cmp(self, a: int, val: int) -> None:
        """CMP: a - val, sets N, Z, C only."""
        self.flag_c = 1 if a >= val else 0
        self._set_nz((a - val) & 0xFF)

    # ----------------------------------------------- Opcode table builder
    def _build_opcode_table(self) -> None:
        self._ops = [None] * 256
        o = self._ops

        # NOP
        o[0x00] = self._op_nop

        # TCALL 0-15
        o[0x01] = self._op_tcall_0
        o[0x11] = self._op_tcall_1
        o[0x21] = self._op_tcall_2
        o[0x31] = self._op_tcall_3
        o[0x41] = self._op_tcall_4
        o[0x51] = self._op_tcall_5
        o[0x61] = self._op_tcall_6
        o[0x71] = self._op_tcall_7
        o[0x81] = self._op_tcall_8
        o[0x91] = self._op_tcall_9
        o[0xA1] = self._op_tcall_10
        o[0xB1] = self._op_tcall_11
        o[0xC1] = self._op_tcall_12
        o[0xD1] = self._op_tcall_13
        o[0xE1] = self._op_tcall_14
        o[0xF1] = self._op_tcall_15

        # SET1 d.0-7
        o[0x02] = self._op_set1_0
        o[0x22] = self._op_set1_1
        o[0x42] = self._op_set1_2
        o[0x62] = self._op_set1_3
        o[0x82] = self._op_set1_4
        o[0xA2] = self._op_set1_5
        o[0xC2] = self._op_set1_6
        o[0xE2] = self._op_set1_7

        # CLR1 d.0-7
        o[0x12] = self._op_clr1_0
        o[0x32] = self._op_clr1_1
        o[0x52] = self._op_clr1_2
        o[0x72] = self._op_clr1_3
        o[0x92] = self._op_clr1_4
        o[0xB2] = self._op_clr1_5
        o[0xD2] = self._op_clr1_6
        o[0xF2] = self._op_clr1_7

        # BBS d.0-7
        o[0x03] = self._op_bbs_0
        o[0x23] = self._op_bbs_1
        o[0x43] = self._op_bbs_2
        o[0x63] = self._op_bbs_3
        o[0x83] = self._op_bbs_4
        o[0xA3] = self._op_bbs_5
        o[0xC3] = self._op_bbs_6
        o[0xE3] = self._op_bbs_7

        # BBC d.0-7
        o[0x13] = self._op_bbc_0
        o[0x33] = self._op_bbc_1
        o[0x53] = self._op_bbc_2
        o[0x73] = self._op_bbc_3
        o[0x93] = self._op_bbc_4
        o[0xB3] = self._op_bbc_5
        o[0xD3] = self._op_bbc_6
        o[0xF3] = self._op_bbc_7

        # OR A,*
        o[0x04] = self._op_or_a_dp
        o[0x05] = self._op_or_a_abs
        o[0x06] = self._op_or_a_ix
        o[0x07] = self._op_or_a_idx
        o[0x08] = self._op_or_a_imm
        o[0x14] = self._op_or_a_dpx
        o[0x15] = self._op_or_a_absx
        o[0x16] = self._op_or_a_absy
        o[0x17] = self._op_or_a_idy

        # OR mem
        o[0x09] = self._op_or_dp_dp
        o[0x18] = self._op_or_dp_imm
        o[0x19] = self._op_or_xy

        # Bit ops with carry
        o[0x0A] = self._op_or1
        o[0x2A] = self._op_or1_not
        o[0x4A] = self._op_and1
        o[0x6A] = self._op_and1_not
        o[0x8A] = self._op_eor1
        o[0xAA] = self._op_mov1_c_bit
        o[0xCA] = self._op_mov1_bit_c
        o[0xEA] = self._op_not1

        # ASL
        o[0x0B] = self._op_asl_dp
        o[0x0C] = self._op_asl_abs
        o[0x1B] = self._op_asl_dpx
        o[0x1C] = self._op_asl_a

        # TSET1 / TCLR1
        o[0x0E] = self._op_tset1
        o[0x4E] = self._op_tclr1

        # BRK / PCALL / MOV dp,#imm / MUL / CALL
        o[0x0F] = self._op_brk
        o[0x4F] = self._op_pcall
        o[0x8F] = self._op_mov_dp_imm
        o[0xCF] = self._op_mul
        o[0x3F] = self._op_call

        # Branches
        o[0x10] = self._op_bpl
        o[0x30] = self._op_bmi
        o[0x50] = self._op_bvc
        o[0x70] = self._op_bvs
        o[0x90] = self._op_bcc
        o[0xB0] = self._op_bcs
        o[0xD0] = self._op_bne
        o[0xF0] = self._op_beq
        o[0x2F] = self._op_bra

        # PUSH/POP
        o[0x0D] = self._op_push_psw
        o[0x2D] = self._op_push_a
        o[0x4D] = self._op_push_x
        o[0x6D] = self._op_push_y
        o[0x8E] = self._op_pop_psw
        o[0xAE] = self._op_pop_a
        o[0xCE] = self._op_pop_x
        o[0xEE] = self._op_pop_y

        # JMP / RET / RETI
        o[0x1F] = self._op_jmp_absx
        o[0x5F] = self._op_jmp_abs
        o[0x6F] = self._op_ret
        o[0x7F] = self._op_reti

        # Flag instructions
        o[0x20] = self._op_clrp
        o[0x40] = self._op_setp
        o[0x60] = self._op_clrc
        o[0x80] = self._op_setc
        o[0xA0] = self._op_ei
        o[0xC0] = self._op_di
        o[0xE0] = self._op_clrv
        o[0xED] = self._op_notc

        # AND A,*
        o[0x24] = self._op_and_a_dp
        o[0x25] = self._op_and_a_abs
        o[0x26] = self._op_and_a_ix
        o[0x27] = self._op_and_a_idx
        o[0x28] = self._op_and_a_imm
        o[0x34] = self._op_and_a_dpx
        o[0x35] = self._op_and_a_absx
        o[0x36] = self._op_and_a_absy
        o[0x37] = self._op_and_a_idy

        # AND mem
        o[0x29] = self._op_and_dp_dp
        o[0x38] = self._op_and_dp_imm
        o[0x39] = self._op_and_xy

        # ROL
        o[0x2B] = self._op_rol_dp
        o[0x2C] = self._op_rol_abs
        o[0x3B] = self._op_rol_dpx
        o[0x3C] = self._op_rol_a

        # CBNE / DBNZ
        o[0x2E] = self._op_cbne_dp
        o[0xDE] = self._op_cbne_dpx
        o[0x6E] = self._op_dbnz_dp
        o[0xFE] = self._op_dbnz_y

        # EOR A,*
        o[0x44] = self._op_eor_a_dp
        o[0x45] = self._op_eor_a_abs
        o[0x46] = self._op_eor_a_ix
        o[0x47] = self._op_eor_a_idx
        o[0x48] = self._op_eor_a_imm
        o[0x54] = self._op_eor_a_dpx
        o[0x55] = self._op_eor_a_absx
        o[0x56] = self._op_eor_a_absy
        o[0x57] = self._op_eor_a_idy

        # EOR mem
        o[0x49] = self._op_eor_dp_dp
        o[0x58] = self._op_eor_dp_imm
        o[0x59] = self._op_eor_xy

        # LSR
        o[0x4B] = self._op_lsr_dp
        o[0x4C] = self._op_lsr_abs
        o[0x5B] = self._op_lsr_dpx
        o[0x5C] = self._op_lsr_a

        # CMP A,*
        o[0x64] = self._op_cmp_a_dp
        o[0x65] = self._op_cmp_a_abs
        o[0x66] = self._op_cmp_a_ix
        o[0x67] = self._op_cmp_a_idx
        o[0x68] = self._op_cmp_a_imm
        o[0x74] = self._op_cmp_a_dpx
        o[0x75] = self._op_cmp_a_absx
        o[0x76] = self._op_cmp_a_absy
        o[0x77] = self._op_cmp_a_idy

        # CMP mem
        o[0x69] = self._op_cmp_dp_dp
        o[0x78] = self._op_cmp_dp_imm
        o[0x79] = self._op_cmp_xy

        # ROR
        o[0x6B] = self._op_ror_dp
        o[0x6C] = self._op_ror_abs
        o[0x7B] = self._op_ror_dpx
        o[0x7C] = self._op_ror_a

        # 16-bit word ops
        o[0x1A] = self._op_decw
        o[0x3A] = self._op_incw
        o[0x5A] = self._op_cmpw
        o[0x7A] = self._op_addw
        o[0x9A] = self._op_subw
        o[0xBA] = self._op_movw_ya_dp
        o[0xDA] = self._op_movw_dp_ya

        # ADC A,*
        o[0x84] = self._op_adc_a_dp
        o[0x85] = self._op_adc_a_abs
        o[0x86] = self._op_adc_a_ix
        o[0x87] = self._op_adc_a_idx
        o[0x88] = self._op_adc_a_imm
        o[0x94] = self._op_adc_a_dpx
        o[0x95] = self._op_adc_a_absx
        o[0x96] = self._op_adc_a_absy
        o[0x97] = self._op_adc_a_idy

        # ADC mem
        o[0x89] = self._op_adc_dp_dp
        o[0x98] = self._op_adc_dp_imm
        o[0x99] = self._op_adc_xy

        # DEC dp / DEC abs / DEC dp+X
        o[0x8B] = self._op_dec_dp
        o[0x8C] = self._op_dec_abs
        o[0x9B] = self._op_dec_dpx
        o[0x9C] = self._op_dec_a
        o[0x1D] = self._op_dec_x
        o[0xDC] = self._op_dec_y

        # MOV Y,*
        o[0x8D] = self._op_mov_y_imm
        o[0xEB] = self._op_mov_y_dp
        o[0xFB] = self._op_mov_y_dpx
        o[0xEC] = self._op_mov_y_abs

        # DIV
        o[0x9E] = self._op_div

        # XCN
        o[0x9F] = self._op_xcn

        # SBC A,*
        o[0xA4] = self._op_sbc_a_dp
        o[0xA5] = self._op_sbc_a_abs
        o[0xA6] = self._op_sbc_a_ix
        o[0xA7] = self._op_sbc_a_idx
        o[0xA8] = self._op_sbc_a_imm
        o[0xB4] = self._op_sbc_a_dpx
        o[0xB5] = self._op_sbc_a_absx
        o[0xB6] = self._op_sbc_a_absy
        o[0xB7] = self._op_sbc_a_idy

        # SBC mem
        o[0xA9] = self._op_sbc_dp_dp
        o[0xB8] = self._op_sbc_dp_imm
        o[0xB9] = self._op_sbc_xy

        # INC dp / INC abs / INC dp+X
        o[0xAB] = self._op_inc_dp
        o[0xAC] = self._op_inc_abs
        o[0xBB] = self._op_inc_dpx
        o[0xBC] = self._op_inc_a
        o[0x3D] = self._op_inc_x
        o[0xFC] = self._op_inc_y

        # CMP X,*  / CMP Y,*
        o[0xC8] = self._op_cmp_x_imm
        o[0x3E] = self._op_cmp_x_dp
        o[0x1E] = self._op_cmp_x_abs
        o[0xAD] = self._op_cmp_y_imm
        o[0x7E] = self._op_cmp_y_dp
        o[0x5E] = self._op_cmp_y_abs

        # MOV A,* (loads)
        o[0xE4] = self._op_mov_a_dp
        o[0xE5] = self._op_mov_a_abs
        o[0xE6] = self._op_mov_a_ix
        o[0xE7] = self._op_mov_a_idx
        o[0xE8] = self._op_mov_a_imm
        o[0xF4] = self._op_mov_a_dpx
        o[0xF5] = self._op_mov_a_absx
        o[0xF6] = self._op_mov_a_absy
        o[0xF7] = self._op_mov_a_idy
        o[0xBF] = self._op_mov_a_ixinc

        # MOV *,A (stores)
        o[0xC4] = self._op_mov_dp_a
        o[0xD4] = self._op_mov_dpx_a
        o[0xC5] = self._op_mov_abs_a
        o[0xD5] = self._op_mov_absx_a
        o[0xD6] = self._op_mov_absy_a
        o[0xC6] = self._op_mov_ix_a
        o[0xC7] = self._op_mov_idx_a
        o[0xD7] = self._op_mov_idy_a
        o[0xAF] = self._op_mov_ixinc_a

        # MOV X,*
        o[0xCD] = self._op_mov_x_imm
        o[0xF8] = self._op_mov_x_dp
        o[0xF9] = self._op_mov_x_dpy
        o[0xE9] = self._op_mov_x_abs
        o[0x5D] = self._op_mov_x_a
        o[0x9D] = self._op_mov_x_sp

        # MOV *,X (stores)
        o[0xD8] = self._op_mov_dp_x
        o[0xD9] = self._op_mov_dpy_x
        o[0xC9] = self._op_mov_abs_x

        # MOV Y,A / MOV A,X / MOV A,Y
        o[0xFD] = self._op_mov_y_a
        o[0x7D] = self._op_mov_a_x
        o[0xDD] = self._op_mov_a_y

        # MOV *,Y (stores)
        o[0xCB] = self._op_mov_dp_y
        o[0xDB] = self._op_mov_dpx_y
        o[0xCC] = self._op_mov_abs_y

        # MOV SP,X
        o[0xBD] = self._op_mov_sp_x

        # MOV dp,dp ($FA)
        o[0xFA] = self._op_mov_dp_dp

        # DAA / DAS
        o[0xDF] = self._op_daa
        o[0xBE] = self._op_das

        # SLEEP / STOP
        o[0xEF] = self._op_sleep
        o[0xFF] = self._op_stop

    # ============================================================ OPCODES

    # --- NOP ---
    def _op_nop(self) -> int:
        return 2

    # --- TCALL 0-15 (direct methods, no closures) ---
    def _tcall(self, vec: int) -> int:
        self._push16(self.pc)
        lo = self.read(vec)
        hi = self.read((vec + 1) & 0xFFFF)
        self.pc = (hi << 8) | lo
        return 8

    def _op_tcall_0(self) -> int: return self._tcall(0xFFDE)
    def _op_tcall_1(self) -> int: return self._tcall(0xFFDC)
    def _op_tcall_2(self) -> int: return self._tcall(0xFFDA)
    def _op_tcall_3(self) -> int: return self._tcall(0xFFD8)
    def _op_tcall_4(self) -> int: return self._tcall(0xFFD6)
    def _op_tcall_5(self) -> int: return self._tcall(0xFFD4)
    def _op_tcall_6(self) -> int: return self._tcall(0xFFD2)
    def _op_tcall_7(self) -> int: return self._tcall(0xFFD0)
    def _op_tcall_8(self) -> int: return self._tcall(0xFFCE)
    def _op_tcall_9(self) -> int: return self._tcall(0xFFCC)
    def _op_tcall_10(self) -> int: return self._tcall(0xFFCA)
    def _op_tcall_11(self) -> int: return self._tcall(0xFFC8)
    def _op_tcall_12(self) -> int: return self._tcall(0xFFC6)
    def _op_tcall_13(self) -> int: return self._tcall(0xFFC4)
    def _op_tcall_14(self) -> int: return self._tcall(0xFFC2)
    def _op_tcall_15(self) -> int: return self._tcall(0xFFC0)

    # --- SET1/CLR1 (direct methods, no closures) ---
    def _op_set1_0(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x01); return 4
    def _op_set1_1(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x02); return 4
    def _op_set1_2(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x04); return 4
    def _op_set1_3(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x08); return 4
    def _op_set1_4(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x10); return 4
    def _op_set1_5(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x20); return 4
    def _op_set1_6(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x40); return 4
    def _op_set1_7(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) | 0x80); return 4

    def _op_clr1_0(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xFE); return 4
    def _op_clr1_1(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xFD); return 4
    def _op_clr1_2(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xFB); return 4
    def _op_clr1_3(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xF7); return 4
    def _op_clr1_4(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xEF); return 4
    def _op_clr1_5(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xDF); return 4
    def _op_clr1_6(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0xBF); return 4
    def _op_clr1_7(self) -> int:
        a = self._dp_addr(self._fetch()); self.write(a, self.read(a) & 0x7F); return 4

    # --- BBS/BBC (direct methods, no closures) ---
    def _bbs(self, mask: int) -> int:
        val = self.read(self._dp_addr(self._fetch()))
        offset = self._fetch()
        if val & mask:
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 7
        return 5

    def _bbc(self, mask: int) -> int:
        val = self.read(self._dp_addr(self._fetch()))
        offset = self._fetch()
        if not (val & mask):
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 7
        return 5

    def _op_bbs_0(self) -> int: return self._bbs(0x01)
    def _op_bbs_1(self) -> int: return self._bbs(0x02)
    def _op_bbs_2(self) -> int: return self._bbs(0x04)
    def _op_bbs_3(self) -> int: return self._bbs(0x08)
    def _op_bbs_4(self) -> int: return self._bbs(0x10)
    def _op_bbs_5(self) -> int: return self._bbs(0x20)
    def _op_bbs_6(self) -> int: return self._bbs(0x40)
    def _op_bbs_7(self) -> int: return self._bbs(0x80)

    def _op_bbc_0(self) -> int: return self._bbc(0x01)
    def _op_bbc_1(self) -> int: return self._bbc(0x02)
    def _op_bbc_2(self) -> int: return self._bbc(0x04)
    def _op_bbc_3(self) -> int: return self._bbc(0x08)
    def _op_bbc_4(self) -> int: return self._bbc(0x10)
    def _op_bbc_5(self) -> int: return self._bbc(0x20)
    def _op_bbc_6(self) -> int: return self._bbc(0x40)
    def _op_bbc_7(self) -> int: return self._bbc(0x80)

    # --- OR A,* ---
    def _op_or_a_dp(self) -> int:
        self.a |= self.read(self._dp_addr(self._fetch())); self._set_nz(self.a); return 3
    def _op_or_a_abs(self) -> int:
        self.a |= self.read(self._fetch16()); self._set_nz(self.a); return 4
    def _op_or_a_ix(self) -> int:
        self.a |= self.read(self._dp_addr(self.x)); self._set_nz(self.a); return 3
    def _op_or_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a |= self.read(((hi << 8) | lo) & 0xFFFF); self._set_nz(self.a); return 6
    def _op_or_a_imm(self) -> int:
        self.a |= self._fetch(); self._set_nz(self.a); return 2
    def _op_or_a_dpx(self) -> int:
        self.a |= self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF); self._set_nz(self.a); return 4
    def _op_or_a_absx(self) -> int:
        self.a |= self.read((self._fetch16() + self.x) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_or_a_absy(self) -> int:
        self.a |= self.read((self._fetch16() + self.y) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_or_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a |= self.read((((hi << 8) | lo) + self.y) & 0xFFFF); self._set_nz(self.a); return 6

    # --- OR mem ---
    def _op_or_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        r = self.read(addr) | val; self.write(addr, r); self._set_nz(r); return 5
    def _op_or_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        r = self.read(da) | self.read(sa); self.write(da, r); self._set_nz(r); return 6
    def _op_or_xy(self) -> int:
        r = self.read(self._dp_addr(self.x)) | self.read(self._dp_addr(self.y))
        self.write(self._dp_addr(self.x), r); self._set_nz(r); return 5

    # --- AND A,* ---
    def _op_and_a_dp(self) -> int:
        self.a &= self.read(self._dp_addr(self._fetch())); self._set_nz(self.a); return 3
    def _op_and_a_abs(self) -> int:
        self.a &= self.read(self._fetch16()); self._set_nz(self.a); return 4
    def _op_and_a_ix(self) -> int:
        self.a &= self.read(self._dp_addr(self.x)); self._set_nz(self.a); return 3
    def _op_and_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a &= self.read(((hi << 8) | lo) & 0xFFFF); self._set_nz(self.a); return 6
    def _op_and_a_imm(self) -> int:
        self.a &= self._fetch(); self._set_nz(self.a); return 2
    def _op_and_a_dpx(self) -> int:
        self.a &= self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF); self._set_nz(self.a); return 4
    def _op_and_a_absx(self) -> int:
        self.a &= self.read((self._fetch16() + self.x) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_and_a_absy(self) -> int:
        self.a &= self.read((self._fetch16() + self.y) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_and_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a &= self.read((((hi << 8) | lo) + self.y) & 0xFFFF); self._set_nz(self.a); return 6

    # --- AND mem ---
    def _op_and_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        r = self.read(addr) & val; self.write(addr, r); self._set_nz(r); return 5
    def _op_and_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        r = self.read(da) & self.read(sa); self.write(da, r); self._set_nz(r); return 6
    def _op_and_xy(self) -> int:
        r = self.read(self._dp_addr(self.x)) & self.read(self._dp_addr(self.y))
        self.write(self._dp_addr(self.x), r); self._set_nz(r); return 5

    # --- EOR A,* ---
    def _op_eor_a_dp(self) -> int:
        self.a ^= self.read(self._dp_addr(self._fetch())); self._set_nz(self.a); return 3
    def _op_eor_a_abs(self) -> int:
        self.a ^= self.read(self._fetch16()); self._set_nz(self.a); return 4
    def _op_eor_a_ix(self) -> int:
        self.a ^= self.read(self._dp_addr(self.x)); self._set_nz(self.a); return 3
    def _op_eor_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a ^= self.read(((hi << 8) | lo) & 0xFFFF); self._set_nz(self.a); return 6
    def _op_eor_a_imm(self) -> int:
        self.a ^= self._fetch(); self._set_nz(self.a); return 2
    def _op_eor_a_dpx(self) -> int:
        self.a ^= self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF); self._set_nz(self.a); return 4
    def _op_eor_a_absx(self) -> int:
        self.a ^= self.read((self._fetch16() + self.x) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_eor_a_absy(self) -> int:
        self.a ^= self.read((self._fetch16() + self.y) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_eor_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a ^= self.read((((hi << 8) | lo) + self.y) & 0xFFFF); self._set_nz(self.a); return 6

    # --- EOR mem ---
    def _op_eor_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        r = self.read(addr) ^ val; self.write(addr, r); self._set_nz(r); return 5
    def _op_eor_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        r = self.read(da) ^ self.read(sa); self.write(da, r); self._set_nz(r); return 6
    def _op_eor_xy(self) -> int:
        r = self.read(self._dp_addr(self.x)) ^ self.read(self._dp_addr(self.y))
        self.write(self._dp_addr(self.x), r); self._set_nz(r); return 5

    # --- ADC A,* ---
    def _op_adc_a_dp(self) -> int:
        self.a = self._adc(self.a, self.read(self._dp_addr(self._fetch()))); return 3
    def _op_adc_a_abs(self) -> int:
        self.a = self._adc(self.a, self.read(self._fetch16())); return 4
    def _op_adc_a_ix(self) -> int:
        self.a = self._adc(self.a, self.read(self._dp_addr(self.x))); return 3
    def _op_adc_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a = self._adc(self.a, self.read(((hi << 8) | lo) & 0xFFFF)); return 6
    def _op_adc_a_imm(self) -> int:
        self.a = self._adc(self.a, self._fetch()); return 2
    def _op_adc_a_dpx(self) -> int:
        self.a = self._adc(self.a, self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF)); return 4
    def _op_adc_a_absx(self) -> int:
        self.a = self._adc(self.a, self.read((self._fetch16() + self.x) & 0xFFFF)); return 5
    def _op_adc_a_absy(self) -> int:
        self.a = self._adc(self.a, self.read((self._fetch16() + self.y) & 0xFFFF)); return 5
    def _op_adc_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a = self._adc(self.a, self.read((((hi << 8) | lo) + self.y) & 0xFFFF)); return 6

    # --- ADC mem ---
    def _op_adc_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        dst = self.read(addr)
        self.write(addr, self._adc(dst, val)); return 5
    def _op_adc_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        self.write(da, self._adc(self.read(da), self.read(sa))); return 6
    def _op_adc_xy(self) -> int:
        dst = self.read(self._dp_addr(self.x)); src = self.read(self._dp_addr(self.y))
        self.write(self._dp_addr(self.x), self._adc(dst, src)); return 5

    # --- SBC A,* ---
    def _op_sbc_a_dp(self) -> int:
        self.a = self._sbc(self.a, self.read(self._dp_addr(self._fetch()))); return 3
    def _op_sbc_a_abs(self) -> int:
        self.a = self._sbc(self.a, self.read(self._fetch16())); return 4
    def _op_sbc_a_ix(self) -> int:
        self.a = self._sbc(self.a, self.read(self._dp_addr(self.x))); return 3
    def _op_sbc_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a = self._sbc(self.a, self.read(((hi << 8) | lo) & 0xFFFF)); return 6
    def _op_sbc_a_imm(self) -> int:
        self.a = self._sbc(self.a, self._fetch()); return 2
    def _op_sbc_a_dpx(self) -> int:
        self.a = self._sbc(self.a, self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF)); return 4
    def _op_sbc_a_absx(self) -> int:
        self.a = self._sbc(self.a, self.read((self._fetch16() + self.x) & 0xFFFF)); return 5
    def _op_sbc_a_absy(self) -> int:
        self.a = self._sbc(self.a, self.read((self._fetch16() + self.y) & 0xFFFF)); return 5
    def _op_sbc_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a = self._sbc(self.a, self.read((((hi << 8) | lo) + self.y) & 0xFFFF)); return 6

    # --- SBC mem ---
    def _op_sbc_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        dst = self.read(addr)
        self.write(addr, self._sbc(dst, val)); return 5
    def _op_sbc_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        self.write(da, self._sbc(self.read(da), self.read(sa))); return 6
    def _op_sbc_xy(self) -> int:
        dst = self.read(self._dp_addr(self.x)); src = self.read(self._dp_addr(self.y))
        self.write(self._dp_addr(self.x), self._sbc(dst, src)); return 5

    # --- CMP A,* ---
    def _op_cmp_a_dp(self) -> int:
        self._cmp(self.a, self.read(self._dp_addr(self._fetch()))); return 3
    def _op_cmp_a_abs(self) -> int:
        self._cmp(self.a, self.read(self._fetch16())); return 4
    def _op_cmp_a_ix(self) -> int:
        self._cmp(self.a, self.read(self._dp_addr(self.x))); return 3
    def _op_cmp_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self._cmp(self.a, self.read(((hi << 8) | lo) & 0xFFFF)); return 6
    def _op_cmp_a_imm(self) -> int:
        self._cmp(self.a, self._fetch()); return 2
    def _op_cmp_a_dpx(self) -> int:
        self._cmp(self.a, self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF)); return 4
    def _op_cmp_a_absx(self) -> int:
        self._cmp(self.a, self.read((self._fetch16() + self.x) & 0xFFFF)); return 5
    def _op_cmp_a_absy(self) -> int:
        self._cmp(self.a, self.read((self._fetch16() + self.y) & 0xFFFF)); return 5
    def _op_cmp_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self._cmp(self.a, self.read((((hi << 8) | lo) + self.y) & 0xFFFF)); return 6

    # --- CMP mem ---
    def _op_cmp_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        self._cmp(self.read(addr), val); return 5
    def _op_cmp_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        self._cmp(self.read(da), self.read(sa)); return 6
    def _op_cmp_xy(self) -> int:
        self._cmp(self.read(self._dp_addr(self.x)), self.read(self._dp_addr(self.y))); return 5

    # --- CMP X,* ---
    def _op_cmp_x_imm(self) -> int:
        self._cmp(self.x, self._fetch()); return 2
    def _op_cmp_x_dp(self) -> int:
        self._cmp(self.x, self.read(self._dp_addr(self._fetch()))); return 3
    def _op_cmp_x_abs(self) -> int:
        self._cmp(self.x, self.read(self._fetch16())); return 4

    # --- CMP Y,* ---
    def _op_cmp_y_imm(self) -> int:
        self._cmp(self.y, self._fetch()); return 2
    def _op_cmp_y_dp(self) -> int:
        self._cmp(self.y, self.read(self._dp_addr(self._fetch()))); return 3
    def _op_cmp_y_abs(self) -> int:
        self._cmp(self.y, self.read(self._fetch16())); return 4

    # --- MOV A,* (loads) ---
    def _op_mov_a_dp(self) -> int:
        self.a = self.read(self._dp_addr(self._fetch())); self._set_nz(self.a); return 3
    def _op_mov_a_abs(self) -> int:
        self.a = self.read(self._fetch16()); self._set_nz(self.a); return 4
    def _op_mov_a_ix(self) -> int:
        self.a = self.read(self._dp_addr(self.x)); self._set_nz(self.a); return 3
    def _op_mov_a_idx(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a = self.read(((hi << 8) | lo) & 0xFFFF); self._set_nz(self.a); return 6
    def _op_mov_a_imm(self) -> int:
        self.a = self._fetch(); self._set_nz(self.a); return 2
    def _op_mov_a_dpx(self) -> int:
        self.a = self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF); self._set_nz(self.a); return 4
    def _op_mov_a_absx(self) -> int:
        self.a = self.read((self._fetch16() + self.x) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_mov_a_absy(self) -> int:
        self.a = self.read((self._fetch16() + self.y) & 0xFFFF); self._set_nz(self.a); return 5
    def _op_mov_a_idy(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.a = self.read((((hi << 8) | lo) + self.y) & 0xFFFF); self._set_nz(self.a); return 6
    def _op_mov_a_ixinc(self) -> int:
        self.a = self.read(self._dp_addr(self.x)); self._set_nz(self.a)
        self.x = (self.x + 1) & 0xFF; return 4

    # --- MOV *,A (stores) ---
    def _op_mov_dp_a(self) -> int:
        self.write(self._dp_addr(self._fetch()), self.a); return 4
    def _op_mov_dpx_a(self) -> int:
        self.write((self._dp_addr(self._fetch()) + self.x) & 0xFFFF, self.a); return 5
    def _op_mov_abs_a(self) -> int:
        self.write(self._fetch16(), self.a); return 5
    def _op_mov_absx_a(self) -> int:
        self.write((self._fetch16() + self.x) & 0xFFFF, self.a); return 6
    def _op_mov_absy_a(self) -> int:
        self.write((self._fetch16() + self.y) & 0xFFFF, self.a); return 6
    def _op_mov_ix_a(self) -> int:
        self.write(self._dp_addr(self.x), self.a); return 4
    def _op_mov_idx_a(self) -> int:
        ptr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.write(((hi << 8) | lo) & 0xFFFF, self.a); return 7
    def _op_mov_idy_a(self) -> int:
        ptr = self._dp_addr(self._fetch())
        lo = self.read(ptr); hi = self.read((ptr + 1) & 0xFFFF)
        self.write((((hi << 8) | lo) + self.y) & 0xFFFF, self.a); return 7
    def _op_mov_ixinc_a(self) -> int:
        self.write(self._dp_addr(self.x), self.a)
        self.x = (self.x + 1) & 0xFF; return 4

    # --- MOV X,* ---
    def _op_mov_x_imm(self) -> int:
        self.x = self._fetch(); self._set_nz(self.x); return 2
    def _op_mov_x_dp(self) -> int:
        self.x = self.read(self._dp_addr(self._fetch())); self._set_nz(self.x); return 3
    def _op_mov_x_dpy(self) -> int:
        self.x = self.read((self._dp_addr(self._fetch()) + self.y) & 0xFFFF); self._set_nz(self.x); return 4
    def _op_mov_x_abs(self) -> int:
        self.x = self.read(self._fetch16()); self._set_nz(self.x); return 4
    def _op_mov_x_a(self) -> int:
        self.x = self.a; self._set_nz(self.x); return 2
    def _op_mov_x_sp(self) -> int:
        self.x = self.sp; self._set_nz(self.x); return 2

    # --- MOV *,X ---
    def _op_mov_dp_x(self) -> int:
        self.write(self._dp_addr(self._fetch()), self.x); return 4
    def _op_mov_dpy_x(self) -> int:
        self.write((self._dp_addr(self._fetch()) + self.y) & 0xFFFF, self.x); return 5
    def _op_mov_abs_x(self) -> int:
        self.write(self._fetch16(), self.x); return 5

    # --- MOV Y,* ---
    def _op_mov_y_imm(self) -> int:
        self.y = self._fetch(); self._set_nz(self.y); return 2
    def _op_mov_y_dp(self) -> int:
        self.y = self.read(self._dp_addr(self._fetch())); self._set_nz(self.y); return 3
    def _op_mov_y_dpx(self) -> int:
        self.y = self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF); self._set_nz(self.y); return 4
    def _op_mov_y_abs(self) -> int:
        self.y = self.read(self._fetch16()); self._set_nz(self.y); return 4

    # --- MOV register-to-register ---
    def _op_mov_a_x(self) -> int:
        self.a = self.x; self._set_nz(self.a); return 2
    def _op_mov_a_y(self) -> int:
        self.a = self.y; self._set_nz(self.a); return 2
    def _op_mov_y_a(self) -> int:
        self.y = self.a; self._set_nz(self.y); return 2

    # --- MOV *,Y ---
    def _op_mov_dp_y(self) -> int:
        self.write(self._dp_addr(self._fetch()), self.y); return 4
    def _op_mov_dpx_y(self) -> int:
        self.write((self._dp_addr(self._fetch()) + self.x) & 0xFFFF, self.y); return 5
    def _op_mov_abs_y(self) -> int:
        self.write(self._fetch16(), self.y); return 5

    # --- MOV SP,X ---
    def _op_mov_sp_x(self) -> int:
        self.sp = self.x; return 2

    # --- MOV dp,#imm ---
    def _op_mov_dp_imm(self) -> int:
        val = self._fetch(); addr = self._dp_addr(self._fetch())
        self.write(addr, val); return 5

    # --- MOV dp,dp ($FA) ---
    def _op_mov_dp_dp(self) -> int:
        sa = self._dp_addr(self._fetch()); da = self._dp_addr(self._fetch())
        self.write(da, self.read(sa)); return 5

    # --- Bit operations with carry ---
    def _read_abs_bit(self):
        raw = self._fetch16()
        return raw & 0x1FFF, (raw >> 13) & 7

    def _op_or1(self) -> int:
        addr, bit = self._read_abs_bit()
        if self.read(addr) & (1 << bit):
            self.flag_c = 1
        return 5
    def _op_or1_not(self) -> int:
        addr, bit = self._read_abs_bit()
        if not (self.read(addr) & (1 << bit)):
            self.flag_c = 1
        return 5
    def _op_and1(self) -> int:
        addr, bit = self._read_abs_bit()
        if not (self.read(addr) & (1 << bit)):
            self.flag_c = 0
        return 4
    def _op_and1_not(self) -> int:
        addr, bit = self._read_abs_bit()
        if self.read(addr) & (1 << bit):
            self.flag_c = 0
        return 4
    def _op_eor1(self) -> int:
        addr, bit = self._read_abs_bit()
        if self.read(addr) & (1 << bit):
            self.flag_c = 1 if not self.flag_c else 0
        return 5
    def _op_mov1_c_bit(self) -> int:
        addr, bit = self._read_abs_bit()
        self.flag_c = 1 if (self.read(addr) & (1 << bit)) else 0
        return 4
    def _op_mov1_bit_c(self) -> int:
        addr, bit = self._read_abs_bit()
        v = self.read(addr)
        if self.flag_c:
            self.write(addr, v | (1 << bit))
        else:
            self.write(addr, v & (~(1 << bit) & 0xFF))
        return 6
    def _op_not1(self) -> int:
        addr, bit = self._read_abs_bit()
        self.write(addr, self.read(addr) ^ (1 << bit))
        return 5

    # --- Shift/Rotate ---
    def _op_asl_dp(self) -> int:
        addr = self._dp_addr(self._fetch()); v = self.read(addr)
        self.flag_c = 1 if v & 0x80 else 0
        v = (v << 1) & 0xFF; self.write(addr, v); self._set_nz(v); return 4
    def _op_asl_abs(self) -> int:
        addr = self._fetch16(); v = self.read(addr)
        self.flag_c = 1 if v & 0x80 else 0
        v = (v << 1) & 0xFF; self.write(addr, v); self._set_nz(v); return 5
    def _op_asl_dpx(self) -> int:
        addr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF; v = self.read(addr)
        self.flag_c = 1 if v & 0x80 else 0
        v = (v << 1) & 0xFF; self.write(addr, v); self._set_nz(v); return 5
    def _op_asl_a(self) -> int:
        self.flag_c = 1 if self.a & 0x80 else 0
        self.a = (self.a << 1) & 0xFF; self._set_nz(self.a); return 2

    def _op_lsr_dp(self) -> int:
        addr = self._dp_addr(self._fetch()); v = self.read(addr)
        self.flag_c = 1 if v & 0x01 else 0
        v = (v >> 1) & 0xFF; self.write(addr, v); self._set_nz(v); return 4
    def _op_lsr_abs(self) -> int:
        addr = self._fetch16(); v = self.read(addr)
        self.flag_c = 1 if v & 0x01 else 0
        v = (v >> 1) & 0xFF; self.write(addr, v); self._set_nz(v); return 5
    def _op_lsr_dpx(self) -> int:
        addr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF; v = self.read(addr)
        self.flag_c = 1 if v & 0x01 else 0
        v = (v >> 1) & 0xFF; self.write(addr, v); self._set_nz(v); return 5
    def _op_lsr_a(self) -> int:
        self.flag_c = 1 if self.a & 0x01 else 0
        self.a = (self.a >> 1) & 0xFF; self._set_nz(self.a); return 2

    def _op_rol_dp(self) -> int:
        addr = self._dp_addr(self._fetch()); v = self.read(addr); oc = self.flag_c
        self.flag_c = 1 if v & 0x80 else 0
        v = ((v << 1) & 0xFF) | oc; self.write(addr, v); self._set_nz(v); return 4
    def _op_rol_abs(self) -> int:
        addr = self._fetch16(); v = self.read(addr); oc = self.flag_c
        self.flag_c = 1 if v & 0x80 else 0
        v = ((v << 1) & 0xFF) | oc; self.write(addr, v); self._set_nz(v); return 5
    def _op_rol_dpx(self) -> int:
        addr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF; v = self.read(addr); oc = self.flag_c
        self.flag_c = 1 if v & 0x80 else 0
        v = ((v << 1) & 0xFF) | oc; self.write(addr, v); self._set_nz(v); return 5
    def _op_rol_a(self) -> int:
        oc = self.flag_c; self.flag_c = 1 if self.a & 0x80 else 0
        self.a = ((self.a << 1) & 0xFF) | oc; self._set_nz(self.a); return 2

    def _op_ror_dp(self) -> int:
        addr = self._dp_addr(self._fetch()); v = self.read(addr); oc = self.flag_c
        self.flag_c = 1 if v & 0x01 else 0
        v = ((v >> 1) & 0xFF) | (oc << 7); self.write(addr, v); self._set_nz(v); return 4
    def _op_ror_abs(self) -> int:
        addr = self._fetch16(); v = self.read(addr); oc = self.flag_c
        self.flag_c = 1 if v & 0x01 else 0
        v = ((v >> 1) & 0xFF) | (oc << 7); self.write(addr, v); self._set_nz(v); return 5
    def _op_ror_dpx(self) -> int:
        addr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF; v = self.read(addr); oc = self.flag_c
        self.flag_c = 1 if v & 0x01 else 0
        v = ((v >> 1) & 0xFF) | (oc << 7); self.write(addr, v); self._set_nz(v); return 5
    def _op_ror_a(self) -> int:
        oc = self.flag_c; self.flag_c = 1 if self.a & 0x01 else 0
        self.a = ((self.a >> 1) & 0xFF) | (oc << 7); self._set_nz(self.a); return 2

    # --- INC/DEC registers ---
    def _op_inc_a(self) -> int:
        self.a = (self.a + 1) & 0xFF; self._set_nz(self.a); return 2
    def _op_dec_a(self) -> int:
        self.a = (self.a - 1) & 0xFF; self._set_nz(self.a); return 2
    def _op_inc_x(self) -> int:
        self.x = (self.x + 1) & 0xFF; self._set_nz(self.x); return 2
    def _op_dec_x(self) -> int:
        self.x = (self.x - 1) & 0xFF; self._set_nz(self.x); return 2
    def _op_inc_y(self) -> int:
        self.y = (self.y + 1) & 0xFF; self._set_nz(self.y); return 2
    def _op_dec_y(self) -> int:
        self.y = (self.y - 1) & 0xFF; self._set_nz(self.y); return 2

    # --- INC/DEC memory ---
    def _op_inc_dp(self) -> int:
        addr = self._dp_addr(self._fetch()); v = (self.read(addr) + 1) & 0xFF
        self.write(addr, v); self._set_nz(v); return 4
    def _op_inc_dpx(self) -> int:
        addr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF; v = (self.read(addr) + 1) & 0xFF
        self.write(addr, v); self._set_nz(v); return 5
    def _op_inc_abs(self) -> int:
        addr = self._fetch16(); v = (self.read(addr) + 1) & 0xFF
        self.write(addr, v); self._set_nz(v); return 5
    def _op_dec_dp(self) -> int:
        addr = self._dp_addr(self._fetch()); v = (self.read(addr) - 1) & 0xFF
        self.write(addr, v); self._set_nz(v); return 4
    def _op_dec_dpx(self) -> int:
        addr = (self._dp_addr(self._fetch()) + self.x) & 0xFFFF; v = (self.read(addr) - 1) & 0xFF
        self.write(addr, v); self._set_nz(v); return 5
    def _op_dec_abs(self) -> int:
        addr = self._fetch16(); v = (self.read(addr) - 1) & 0xFF
        self.write(addr, v); self._set_nz(v); return 5

    # --- 16-bit word operations ---
    def _op_addw(self) -> int:
        addr = self._dp_addr(self._fetch())
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        val = (hi << 8) | lo
        ya = (self.y << 8) | self.a
        result = ya + val
        self.flag_h = 1 if ((ya & 0xFFF) + (val & 0xFFF)) > 0xFFF else 0
        self.flag_v = 1 if (~(ya ^ val) & (ya ^ result) & 0x8000) else 0
        self.flag_c = 1 if result > 0xFFFF else 0
        result &= 0xFFFF
        self.a = result & 0xFF
        self.y = (result >> 8) & 0xFF
        self._set_nz16(result)
        return 5

    def _op_subw(self) -> int:
        addr = self._dp_addr(self._fetch())
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        val = (hi << 8) | lo
        ya = (self.y << 8) | self.a
        result = ya - val
        self.flag_h = 1 if ((ya & 0xFFF) - (val & 0xFFF)) >= 0 else 0
        self.flag_v = 1 if ((ya ^ val) & (ya ^ result) & 0x8000) else 0
        self.flag_c = 1 if ya >= val else 0
        result &= 0xFFFF
        self.a = result & 0xFF
        self.y = (result >> 8) & 0xFF
        self._set_nz16(result)
        return 5

    def _op_cmpw(self) -> int:
        addr = self._dp_addr(self._fetch())
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        val = (hi << 8) | lo
        ya = (self.y << 8) | self.a
        self.flag_c = 1 if ya >= val else 0
        self._set_nz16((ya - val) & 0xFFFF)
        return 4

    def _op_incw(self) -> int:
        addr = self._dp_addr(self._fetch())
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        val = ((hi << 8) | lo) + 1
        val &= 0xFFFF
        self.write(addr, val & 0xFF)
        self.write((addr + 1) & 0xFFFF, (val >> 8) & 0xFF)
        self._set_nz16(val)
        return 6

    def _op_decw(self) -> int:
        addr = self._dp_addr(self._fetch())
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        val = ((hi << 8) | lo) - 1
        val &= 0xFFFF
        self.write(addr, val & 0xFF)
        self.write((addr + 1) & 0xFFFF, (val >> 8) & 0xFF)
        self._set_nz16(val)
        return 6

    def _op_movw_ya_dp(self) -> int:
        addr = self._dp_addr(self._fetch())
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        self.a = lo; self.y = hi
        self._set_nz16((hi << 8) | lo)
        return 5

    def _op_movw_dp_ya(self) -> int:
        addr = self._dp_addr(self._fetch())
        self.write(addr, self.a)
        self.write((addr + 1) & 0xFFFF, self.y)
        return 5

    # --- PUSH/POP ---
    def _op_push_a(self) -> int: self._push(self.a); return 4
    def _op_push_x(self) -> int: self._push(self.x); return 4
    def _op_push_y(self) -> int: self._push(self.y); return 4
    def _op_push_psw(self) -> int: self._push(self.get_psw()); return 4
    def _op_pop_a(self) -> int: self.a = self._pop(); return 4
    def _op_pop_x(self) -> int: self.x = self._pop(); return 4
    def _op_pop_y(self) -> int: self.y = self._pop(); return 4
    def _op_pop_psw(self) -> int: self.set_psw(self._pop()); return 4

    # --- TSET1 / TCLR1 ---
    def _op_tset1(self) -> int:
        addr = self._fetch16(); val = self.read(addr)
        self._set_nz((self.a - val) & 0xFF)
        self.write(addr, val | self.a)
        return 6

    def _op_tclr1(self) -> int:
        addr = self._fetch16(); val = self.read(addr)
        self._set_nz((self.a - val) & 0xFF)
        self.write(addr, val & (~self.a & 0xFF))
        return 6

    # --- Branches ---
    def _branch_if(self, cond: bool) -> int:
        offset = self._fetch()
        if cond:
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 4
        return 2

    def _op_bra(self) -> int: return self._branch_if(True)
    def _op_beq(self) -> int: return self._branch_if(self.flag_z == 1)
    def _op_bne(self) -> int: return self._branch_if(self.flag_z == 0)
    def _op_bcs(self) -> int: return self._branch_if(self.flag_c == 1)
    def _op_bcc(self) -> int: return self._branch_if(self.flag_c == 0)
    def _op_bmi(self) -> int: return self._branch_if(self.flag_n == 1)
    def _op_bpl(self) -> int: return self._branch_if(self.flag_n == 0)
    def _op_bvs(self) -> int: return self._branch_if(self.flag_v == 1)
    def _op_bvc(self) -> int: return self._branch_if(self.flag_v == 0)

    # --- CBNE / DBNZ ---
    def _op_cbne_dp(self) -> int:
        val = self.read(self._dp_addr(self._fetch()))
        offset = self._fetch()
        if self.a != val:
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 7
        return 5

    def _op_cbne_dpx(self) -> int:
        val = self.read((self._dp_addr(self._fetch()) + self.x) & 0xFFFF)
        offset = self._fetch()
        if self.a != val:
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 8
        return 6

    def _op_dbnz_dp(self) -> int:
        addr = self._dp_addr(self._fetch())
        val = (self.read(addr) - 1) & 0xFF
        self.write(addr, val)
        offset = self._fetch()
        if val != 0:
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 7
        return 5

    def _op_dbnz_y(self) -> int:
        self.y = (self.y - 1) & 0xFF
        offset = self._fetch()
        if self.y != 0:
            if offset & 0x80:
                self.pc = (self.pc + offset - 256) & 0xFFFF
            else:
                self.pc = (self.pc + offset) & 0xFFFF
            return 6
        return 4

    # --- JMP / CALL / RET ---
    def _op_jmp_abs(self) -> int:
        self.pc = self._fetch16(); return 3
    def _op_jmp_absx(self) -> int:
        addr = (self._fetch16() + self.x) & 0xFFFF
        lo = self.read(addr); hi = self.read((addr + 1) & 0xFFFF)
        self.pc = (hi << 8) | lo; return 6
    def _op_call(self) -> int:
        addr = self._fetch16(); self._push16(self.pc); self.pc = addr; return 8
    def _op_pcall(self) -> int:
        n = self._fetch(); self._push16(self.pc); self.pc = 0xFF00 | n; return 6
    def _op_ret(self) -> int:
        self.pc = self._pop16(); return 5
    def _op_reti(self) -> int:
        self.set_psw(self._pop()); self.pc = self._pop16(); return 6
    def _op_brk(self) -> int:
        self._push16(self.pc); self._push(self.get_psw())
        self.flag_b = 1; self.flag_i = 0
        lo = self.read(0xFFDE); hi = self.read(0xFFDF)
        self.pc = (hi << 8) | lo; return 8

    # --- MUL / DIV ---
    def _op_mul(self) -> int:
        result = self.y * self.a
        self.a = result & 0xFF
        self.y = (result >> 8) & 0xFF
        self._set_nz(self.y)
        return 9

    def _op_div(self) -> int:
        ya = (self.y << 8) | self.a
        if self.x == 0:
            self.flag_v = 1
            self.flag_h = 0
            self.a = 0xFF
            # Y unchanged
        else:
            quotient = ya // self.x
            remainder = ya % self.x
            self.flag_v = 1 if quotient > 0x1FF else 0
            self.flag_h = 1 if (self.x & 0xF) <= (self.y & 0xF) else 0
            self.a = quotient & 0xFF
            self.y = remainder & 0xFF
        self._set_nz(self.a)
        return 12

    # --- XCN ---
    def _op_xcn(self) -> int:
        self.a = ((self.a >> 4) & 0x0F) | ((self.a << 4) & 0xF0)
        self._set_nz(self.a)
        return 5

    # --- DAA / DAS ---
    def _op_daa(self) -> int:
        a = self.a
        if self.flag_c or a > 0x99:
            a = (a + 0x60) & 0xFF
            self.flag_c = 1
        if self.flag_h or (a & 0x0F) > 9:
            a = (a + 0x06) & 0xFF
        self.a = a
        self._set_nz(self.a)
        return 3

    def _op_das(self) -> int:
        a = self.a
        if not self.flag_c or a > 0x99:
            a = (a - 0x60) & 0xFF
            self.flag_c = 0
        if not self.flag_h or (a & 0x0F) > 9:
            a = (a - 0x06) & 0xFF
        self.a = a
        self._set_nz(self.a)
        return 3

    # --- Flag instructions ---
    def _op_clrc(self) -> int: self.flag_c = 0; return 2
    def _op_setc(self) -> int: self.flag_c = 1; return 2
    def _op_notc(self) -> int: self.flag_c = 1 if not self.flag_c else 0; return 3
    def _op_clrp(self) -> int: self.flag_p = 0; return 2
    def _op_setp(self) -> int: self.flag_p = 1; return 2
    def _op_ei(self) -> int: self.flag_i = 1; return 3
    def _op_di(self) -> int: self.flag_i = 0; return 3
    def _op_clrv(self) -> int: self.flag_v = 0; self.flag_h = 0; return 2

    # --- SLEEP / STOP ---
    def _op_sleep(self) -> int: self.halted = True; return 3
    def _op_stop(self) -> int: self.halted = True; return 3

    # ============================================================ EXECUTE
    def step(self) -> int:
        """Execute one instruction, return cycles consumed."""
        if self.halted:
            self._tick_timers(2)
            self.cycles += 2
            return 2  # idle cycles

        opcode = self._fetch()
        handler = self._ops[opcode]
        if handler is None:
            self._tick_timers(2)
            self.cycles += 2
            return 2  # unimplemented opcode — treat as NOP

        cyc = handler()
        self._tick_timers(cyc)
        self.cycles += cyc
        return cyc

    def run_cycles(self, target_cycles: int) -> None:
        """Run until at least target_cycles have been consumed."""
        while self.cycles < target_cycles:
            self.step()
