#ifndef CY7C67200_HPI_H
#define CY7C67200_HPI_H

#include <stdint.h>
#include <stddef.h>

typedef void (*cy_log_fn)(const char *s);
typedef void (*cy_log_hex16_fn)(uint16_t v);
typedef void (*cy_log_hex32_fn)(uint32_t v);
typedef void (*cy_sleep_ms_fn)(uint32_t ms);

typedef struct cy_hpi_ctx {
    uintptr_t base;
    cy_log_fn puts;
    cy_log_hex16_fn puthex16;
    cy_log_hex32_fn puthex32;
    cy_sleep_ms_fn sleep_ms;
} cy_hpi_ctx_t;

#define CY_HPI_DATA_OFFSET       0x000u
#define CY_HPI_MAILBOX_OFFSET    0x004u
#define CY_HPI_ADDRESS_OFFSET    0x008u
#define CY_HPI_STATUS_OFFSET     0x00Cu
#define CY_HPI_CFG0_OFFSET       0x100u
#define CY_HPI_DBG_CTRL_OFFSET   0x104u
#define CY_HPI_DBG_SAMPLE_OFFSET 0x108u
#define CY_HPI_DBG_CY_OFFSET     0x10Cu

#define CY_HPI_CFG(force_rst, rst_n, access, sample, turnaround)     (((force_rst) ? 1u : 0u) | (((rst_n) ? 1u : 0u) << 1) |      (((uint32_t)(access) & 0x3fu) << 2) |      (((uint32_t)(sample) & 0x3fu) << 8) |      (((uint32_t)(turnaround) & 0x3fu) << 14))

#define CY_HPI_DEFAULT_ACCESS_CYCLES      10u
#define CY_HPI_DEFAULT_SAMPLE_OFFSET      2u
#define CY_HPI_DEFAULT_TURNAROUND_CYCLES  2u

static inline volatile uint32_t *cy_hpi_reg32(cy_hpi_ctx_t *ctx, uint32_t off) {
    return (volatile uint32_t *)(ctx->base + off);
}

void cy_hpi_init(cy_hpi_ctx_t *ctx, uintptr_t base, cy_log_fn puts,
                 cy_log_hex16_fn puthex16, cy_log_hex32_fn puthex32,
                 cy_sleep_ms_fn sleep_ms);

void cy_hpi_set_timing(cy_hpi_ctx_t *ctx, uint32_t access_cycles,
                       uint32_t sample_offset, uint32_t turnaround_cycles,
                       int force_reset, int reset_n);

void cy_hpi_reset(cy_hpi_ctx_t *ctx, uint32_t low_ms, uint32_t high_ms);
void cy_hpi_write16(cy_hpi_ctx_t *ctx, uint16_t addr, uint16_t value);
uint16_t cy_hpi_read16(cy_hpi_ctx_t *ctx, uint16_t addr);

void cy_hpi_write_block(cy_hpi_ctx_t *ctx, uint16_t addr,
                        const uint8_t *data, uint16_t len);

uint16_t cy_hpi_mailbox_read(cy_hpi_ctx_t *ctx);
void cy_hpi_mailbox_write(cy_hpi_ctx_t *ctx, uint16_t value);
uint16_t cy_hpi_status_read(cy_hpi_ctx_t *ctx);

void cy_hpi_dump_debug(cy_hpi_ctx_t *ctx, const char *label);
int cy_hpi_basic_reg_probe(cy_hpi_ctx_t *ctx, uint16_t *hwrev,
                           uint16_t *cpu_speed, uint16_t *power_ctl);
int cy_hpi_ram_rw_probe(cy_hpi_ctx_t *ctx, uint16_t addr, uint16_t value,
                        uint16_t *readback);
void cy_hpi_errata_cleanup(cy_hpi_ctx_t *ctx);

#endif
