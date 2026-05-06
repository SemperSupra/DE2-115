#include <stdint.h>
#include "cy7c67200_bringup.h"
#include "cy7c67200_regs.h"
#include "cy7c67200_scan.h"
#include "cy7c67200_lcp.h"

static void log_stage(cy_hpi_ctx_t *ctx, const char *s) {
    if (ctx->puts) ctx->puts(s);
}

static void log_reset_low_read(cy_hpi_ctx_t *ctx, const char *name, uint16_t value) {
    if (!ctx->puts || !ctx->puthex16) return;
    ctx->puts("CY_STAGE0_RESET_LOW_READ ");
    ctx->puts(name);
    ctx->puts("=");
    ctx->puthex16(value);
    ctx->puts("\n");
}

static uint32_t manual_ctrl_word(int force_en, int rd_n, int wr_n, int cs_n, uint16_t addr) {
    return ((force_en ? 1u : 0u) |
            ((rd_n ? 1u : 0u) << 1) |
            ((wr_n ? 1u : 0u) << 2) |
            ((cs_n ? 1u : 0u) << 3) |
            (((uint32_t)addr & 0x3u) << 4));
}

static void log_manual_sample(cy_hpi_ctx_t *ctx, const char *label) {
    if (!ctx->puts || !ctx->puthex16 || !ctx->puthex32) return;
    uint32_t ctrl = *cy_hpi_reg32(ctx, CY_HPI_MANUAL_CTRL_OFFSET);
    uint16_t sample = (uint16_t)(*cy_hpi_reg32(ctx, CY_HPI_MANUAL_SAMPLE_OFFSET) & 0xffffu);
    uint16_t cy = (uint16_t)(*cy_hpi_reg32(ctx, CY_HPI_MANUAL_CY_OFFSET) & 0xffffu);

    ctx->puts("CY_STAGE0_MANUAL ");
    ctx->puts(label);
    ctx->puts(" ctrl=");
    ctx->puthex32(ctrl);
    ctx->puts(" sample=");
    ctx->puthex16(sample);
    ctx->puts(" cy=");
    ctx->puthex16(cy);
    ctx->puts("\n");
}

static void write_manual_ctrl(cy_hpi_ctx_t *ctx, int force_en, int rd_n,
                              int wr_n, int cs_n, uint16_t addr) {
    *cy_hpi_reg32(ctx, CY_HPI_MANUAL_CTRL_OFFSET) =
        manual_ctrl_word(force_en, rd_n, wr_n, cs_n, addr);
}

static void set_manual_ctrl_delay(cy_hpi_ctx_t *ctx, const char *label,
                                  int force_en, int rd_n, int wr_n, int cs_n,
                                  uint16_t addr, uint32_t delay_ms) {
    write_manual_ctrl(ctx, force_en, rd_n, wr_n, cs_n, addr);
    if (delay_ms && ctx->sleep_ms) ctx->sleep_ms(delay_ms);
    log_manual_sample(ctx, label);
}

static void cy_stage0_manual_pin_sweep(cy_hpi_ctx_t *ctx) {
    *cy_hpi_reg32(ctx, CY_HPI_MANUAL_DATA_OFFSET) = 0xa5a5u;
    set_manual_ctrl_delay(ctx, "idle", 1, 1, 1, 1, 0, 2u);
    set_manual_ctrl_delay(ctx, "cs_only", 1, 1, 1, 0, 0, 2u);
    set_manual_ctrl_delay(ctx, "rd_only", 1, 0, 1, 1, 0, 2u);
    set_manual_ctrl_delay(ctx, "read_data", 1, 0, 1, 0, 0, 2u);
    set_manual_ctrl_delay(ctx, "read_mailbox", 1, 0, 1, 0, 1, 2u);
    set_manual_ctrl_delay(ctx, "read_address", 1, 0, 1, 0, 2, 2u);
    set_manual_ctrl_delay(ctx, "read_status", 1, 0, 1, 0, 3, 2u);
    set_manual_ctrl_delay(ctx, "write_drive", 1, 1, 0, 0, 0, 2u);
    set_manual_ctrl_delay(ctx, "released", 0, 1, 1, 1, 0, 2u);
}

static void cy_stage0_manual_edge_sweep(cy_hpi_ctx_t *ctx) {
    *cy_hpi_reg32(ctx, CY_HPI_MANUAL_DATA_OFFSET) = 0xa5a5u;

    set_manual_ctrl_delay(ctx, "edge_idle", 1, 1, 1, 1, 0, 2u);
    set_manual_ctrl_delay(ctx, "edge_read_hold", 1, 0, 1, 0, 0, 5u);
    set_manual_ctrl_delay(ctx, "edge_rd_hi_0ms", 1, 1, 1, 0, 0, 0u);
    set_manual_ctrl_delay(ctx, "edge_rd_hi_1ms", 1, 1, 1, 0, 0, 1u);
    set_manual_ctrl_delay(ctx, "edge_rd_hi_10ms", 1, 1, 1, 0, 0, 10u);

    set_manual_ctrl_delay(ctx, "edge_read_hold2", 1, 0, 1, 0, 0, 5u);
    set_manual_ctrl_delay(ctx, "edge_cs_hi_0ms", 1, 0, 1, 1, 0, 0u);
    set_manual_ctrl_delay(ctx, "edge_cs_hi_1ms", 1, 0, 1, 1, 0, 1u);
    set_manual_ctrl_delay(ctx, "edge_cs_hi_10ms", 1, 0, 1, 1, 0, 10u);

    set_manual_ctrl_delay(ctx, "order_idle", 1, 1, 1, 1, 0, 2u);
    set_manual_ctrl_delay(ctx, "order_cs_first", 1, 1, 1, 0, 0, 2u);
    set_manual_ctrl_delay(ctx, "order_cs_rd", 1, 0, 1, 0, 0, 2u);
    set_manual_ctrl_delay(ctx, "order_release", 1, 1, 1, 1, 0, 2u);
    set_manual_ctrl_delay(ctx, "order_rd_first", 1, 0, 1, 1, 0, 2u);
    set_manual_ctrl_delay(ctx, "order_rd_cs", 1, 0, 1, 0, 0, 2u);
    set_manual_ctrl_delay(ctx, "edge_released", 0, 1, 1, 1, 0, 2u);
}

static void cy_stage0_reset_low_active_read_probe(cy_hpi_ctx_t *ctx) {
    cy_hpi_set_timing(ctx, 63u, 8u, 8u, 1, 0);
    if (ctx->sleep_ms) ctx->sleep_ms(10u);
    cy_hpi_dump_debug(ctx, "CY_STAGE0_RESET_LOW_IDLE");
    cy_stage0_manual_pin_sweep(ctx);
    cy_stage0_manual_edge_sweep(ctx);

    uint16_t data = cy_hpi_read16(ctx, 0x1000u);
    log_reset_low_read(ctx, "data", data);
    cy_hpi_dump_debug(ctx, "CY_STAGE0_RESET_LOW_DATA_DBG");

    uint16_t mailbox = cy_hpi_mailbox_read(ctx);
    log_reset_low_read(ctx, "mailbox", mailbox);
    cy_hpi_dump_debug(ctx, "CY_STAGE0_RESET_LOW_MAILBOX_DBG");

    uint16_t status = cy_hpi_status_read(ctx);
    log_reset_low_read(ctx, "status", status);
    cy_hpi_dump_debug(ctx, "CY_STAGE0_RESET_LOW_STATUS_DBG");
}

cy_bringup_result_t cy_bringup_run(cy_hpi_ctx_t *ctx,
                                   const cy_bringup_blobs_t *blobs,
                                   int stop_on_failure) {
    uint16_t hwrev = 0, cpu = 0, pwr = 0;
    uint16_t rb = 0;
    cy_bringup_result_t first_failure = CY_BRINGUP_OK;

    log_stage(ctx, "CY_STAGE0_FPGA_HPI_BRIDGE_START\n");
    cy_hpi_set_timing(ctx, CY_HPI_DEFAULT_ACCESS_CYCLES,
                      CY_HPI_DEFAULT_SAMPLE_OFFSET,
                      CY_HPI_DEFAULT_TURNAROUND_CYCLES, 1, 0);
    cy_hpi_dump_debug(ctx, "CY_STAGE0_DBG");
    cy_stage0_reset_low_active_read_probe(ctx);
    log_stage(ctx, "CY_STAGE0_FPGA_HPI_BRIDGE_PASS\n");

    log_stage(ctx, "CY_STAGE1_RESET_RELEASE_START\n");
    cy_hpi_reset(ctx, 250u, 500u);
    log_stage(ctx, "CY_STAGE1_RESET_RELEASE_PASS\n");

    log_stage(ctx, "CY_STAGE2_REG_READ_START\n");
    int reg_ok = cy_hpi_basic_reg_probe(ctx, &hwrev, &cpu, &pwr);
    if (ctx->puts && ctx->puthex16) {
        ctx->puts("CY_STAGE2_REG_READ_VALUES hwrev=");
        ctx->puthex16(hwrev);
        ctx->puts(" cpu=");
        ctx->puthex16(cpu);
        ctx->puts(" pwr=");
        ctx->puthex16(pwr);
        ctx->puts("\n");
    }
    if (!reg_ok) {
        log_stage(ctx, "CY_STAGE2_REG_READ_FAIL\n");
        if (first_failure == CY_BRINGUP_OK) first_failure = CY_BRINGUP_FAIL_REG_READ;
        if (stop_on_failure) return first_failure;
    } else {
        log_stage(ctx, "CY_STAGE2_REG_READ_PASS\n");
    }

    log_stage(ctx, "CY_STAGE3_RAM_RW_START\n");
    int ram_ok = cy_hpi_ram_rw_probe(ctx, 0x1000u, 0x1234u, &rb);
    if (ctx->puts && ctx->puthex16) {
        ctx->puts("CY_STAGE3_RAM_RW_VALUE read=");
        ctx->puthex16(rb);
        ctx->puts("\n");
    }
    if (!ram_ok) {
        log_stage(ctx, "CY_STAGE3_RAM_RW_FAIL\n");
        if (first_failure == CY_BRINGUP_OK) first_failure = CY_BRINGUP_FAIL_RAM_RW;
        if (stop_on_failure) return first_failure;
    } else {
        log_stage(ctx, "CY_STAGE3_RAM_RW_PASS\n");
    }

    log_stage(ctx, "CY_STAGE4_ERRATA_CLEANUP_START\n");
    if (ctx->sleep_ms) ctx->sleep_ms(10u);
    cy_hpi_errata_cleanup(ctx);
    log_stage(ctx, "CY_STAGE4_ERRATA_CLEANUP_DONE\n");

    log_stage(ctx, "CY_STAGE4B_LCP_HANDSHAKE_START\n");
    cy_hpi_mailbox_write(ctx, CY_COMM_RESET);
    int lcp_ok = 0;
    for (int i = 0; i < 1000; i++) {
        if (cy_hpi_status_read(ctx) & CY_HPI_STATUS_MAILBOX_OUT) {
            uint16_t mbx = cy_hpi_mailbox_read(ctx);
            if (mbx == CY_COMM_ACK) {
                lcp_ok = 1;
                break;
            }
        }
        if (ctx->sleep_ms) ctx->sleep_ms(1u);
    }
    if (!lcp_ok) {
        log_stage(ctx, "CY_STAGE4B_LCP_HANDSHAKE_FAIL\n");
        if (first_failure == CY_BRINGUP_OK) first_failure = CY_BRINGUP_FAIL_LCP_HANDSHAKE;
        if (stop_on_failure) return first_failure;
    } else {
        log_stage(ctx, "CY_STAGE4B_LCP_HANDSHAKE_PASS\n");
    }

    if (blobs && blobs->scan_image && blobs->scan_image_len) {
        cy_scan_stats_t stats;
        log_stage(ctx, "CY_STAGE5_SCAN_COPY_START\n");
        if (!cy_scan_execute_over_hpi(ctx, blobs->scan_image, blobs->scan_image_len, &stats, 0)) {
            log_stage(ctx, "CY_STAGE5_SCAN_COPY_FAIL\n");
            if (first_failure == CY_BRINGUP_OK) first_failure = CY_BRINGUP_FAIL_SCAN;
            if (stop_on_failure) return first_failure;
        } else if (ctx->puts && ctx->puthex32) {
            ctx->puts("CY_STAGE5_SCAN_COPY_PASS records=");
            ctx->puthex32(stats.records);
            ctx->puts(" bytes=");
            ctx->puthex32(stats.bytes_copied);
            ctx->puts("\n");
        }
    } else {
        log_stage(ctx, "CY_STAGE5_SCAN_COPY_SKIP\n");
    }

    if (blobs && blobs->lcp_probe_call_addr) {
        log_stage(ctx, "CY_STAGE6_LCP_CALL_START\n");
        if (!cy_lcp_call_code(ctx, blobs->lcp_probe_call_addr, 1000000u)) {
            log_stage(ctx, "CY_STAGE6_LCP_CALL_FAIL\n");
            if (first_failure == CY_BRINGUP_OK) first_failure = CY_BRINGUP_FAIL_LCP;
            if (stop_on_failure) return first_failure;
        } else {
            log_stage(ctx, "CY_STAGE6_LCP_CALL_PASS\n");
        }
    } else {
        log_stage(ctx, "CY_STAGE6_LCP_CALL_SKIP\n");
    }

    log_stage(ctx, "CY_STAGE7_BIOS_INT_SKIP\n");
    return first_failure;
}
