#include "cy7c67200_hpi.h"
#include "cy7c67200_regs.h"

void cy_hpi_init(cy_hpi_ctx_t *ctx, uintptr_t base, cy_log_fn puts,
                 cy_log_hex16_fn puthex16, cy_log_hex32_fn puthex32,
                 cy_sleep_ms_fn sleep_ms) {
    ctx->base = base;
    ctx->puts = puts;
    ctx->puthex16 = puthex16;
    ctx->puthex32 = puthex32;
    ctx->sleep_ms = sleep_ms;
}

void cy_hpi_set_timing(cy_hpi_ctx_t *ctx, uint32_t access_cycles,
                       uint32_t sample_offset, uint32_t turnaround_cycles,
                       int force_reset, int reset_n) {
    *cy_hpi_reg32(ctx, CY_HPI_CFG0_OFFSET) =
        CY_HPI_CFG(force_reset, reset_n, access_cycles, sample_offset, turnaround_cycles);
}

void cy_hpi_reset(cy_hpi_ctx_t *ctx, uint32_t low_ms, uint32_t high_ms) {
    cy_hpi_set_timing(ctx,
        CY_HPI_DEFAULT_ACCESS_CYCLES,
        CY_HPI_DEFAULT_SAMPLE_OFFSET,
        CY_HPI_DEFAULT_TURNAROUND_CYCLES,
        1, 0);
    if (ctx->sleep_ms) ctx->sleep_ms(low_ms);

    cy_hpi_set_timing(ctx,
        CY_HPI_DEFAULT_ACCESS_CYCLES,
        CY_HPI_DEFAULT_SAMPLE_OFFSET,
        CY_HPI_DEFAULT_TURNAROUND_CYCLES,
        1, 1);
    if (ctx->sleep_ms) ctx->sleep_ms(high_ms);
}

void cy_hpi_write16(cy_hpi_ctx_t *ctx, uint16_t addr, uint16_t value) {
    *cy_hpi_reg32(ctx, CY_HPI_ADDRESS_OFFSET) = addr;
    *cy_hpi_reg32(ctx, CY_HPI_DATA_OFFSET) = value;
}

uint16_t cy_hpi_read16(cy_hpi_ctx_t *ctx, uint16_t addr) {
    *cy_hpi_reg32(ctx, CY_HPI_ADDRESS_OFFSET) = addr;
    return (uint16_t)(*cy_hpi_reg32(ctx, CY_HPI_DATA_OFFSET) & 0xFFFFu);
}

void cy_hpi_write_block(cy_hpi_ctx_t *ctx, uint16_t addr,
                        const uint8_t *data, uint16_t len) {
    *cy_hpi_reg32(ctx, CY_HPI_ADDRESS_OFFSET) = addr;
    for (uint16_t i = 0; i < len; i += 2) {
        uint16_t lo = data[i];
        uint16_t hi = (i + 1u < len) ? ((uint16_t)data[i + 1u] << 8) : 0u;
        *cy_hpi_reg32(ctx, CY_HPI_DATA_OFFSET) = lo | hi;
    }
}

uint16_t cy_hpi_mailbox_read(cy_hpi_ctx_t *ctx) {
    return (uint16_t)(*cy_hpi_reg32(ctx, CY_HPI_MAILBOX_OFFSET) & 0xFFFFu);
}

void cy_hpi_mailbox_write(cy_hpi_ctx_t *ctx, uint16_t value) {
    *cy_hpi_reg32(ctx, CY_HPI_MAILBOX_OFFSET) = value;
}

uint16_t cy_hpi_status_read(cy_hpi_ctx_t *ctx) {
    return (uint16_t)(*cy_hpi_reg32(ctx, CY_HPI_STATUS_OFFSET) & 0xFFFFu);
}

void cy_hpi_dump_debug(cy_hpi_ctx_t *ctx, const char *label) {
    if (!ctx->puts || !ctx->puthex32) return;
    ctx->puts(label);
    ctx->puts(" cfg=");
    ctx->puthex32(*cy_hpi_reg32(ctx, CY_HPI_CFG0_OFFSET));
    ctx->puts(" ctrl=");
    ctx->puthex32(*cy_hpi_reg32(ctx, CY_HPI_DBG_CTRL_OFFSET));
    ctx->puts(" sample=");
    ctx->puthex32(*cy_hpi_reg32(ctx, CY_HPI_DBG_SAMPLE_OFFSET));
    ctx->puts(" cy=");
    ctx->puthex32(*cy_hpi_reg32(ctx, CY_HPI_DBG_CY_OFFSET));
    ctx->puts("\n");
}

int cy_hpi_basic_reg_probe(cy_hpi_ctx_t *ctx, uint16_t *hwrev,
                           uint16_t *cpu_speed, uint16_t *power_ctl) {
    *hwrev = cy_hpi_read16(ctx, CY_HW_REV_REG);
    *cpu_speed = cy_hpi_read16(ctx, CY_CPU_SPEED_REG);
    *power_ctl = cy_hpi_read16(ctx, CY_POWER_CTL_REG);
    return ((*hwrev | *cpu_speed | *power_ctl) != 0u);
}

int cy_hpi_ram_rw_probe(cy_hpi_ctx_t *ctx, uint16_t addr, uint16_t value,
                        uint16_t *readback) {
    cy_hpi_write16(ctx, addr, value);
    cy_hpi_dump_debug(ctx, "HPI DBG WR");
    *readback = cy_hpi_read16(ctx, addr);
    cy_hpi_dump_debug(ctx, "HPI DBG RD");
    return (*readback == value);
}

void cy_hpi_errata_cleanup(cy_hpi_ctx_t *ctx) {
    cy_hpi_write16(ctx, CY_SIE1MSG_REG, 0x0000u);
    cy_hpi_write16(ctx, CY_SIE2MSG_REG, 0x0000u);
    (void)cy_hpi_read16(ctx, CY_SIE1MSG_REG);
    (void)cy_hpi_read16(ctx, CY_SIE2MSG_REG);
}
