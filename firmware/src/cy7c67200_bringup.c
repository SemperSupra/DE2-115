#include <stdint.h>
#include "cy7c67200_bringup.h"
#include "cy7c67200_regs.h"
#include "cy7c67200_scan.h"
#include "cy7c67200_lcp.h"

static void log_stage(cy_hpi_ctx_t *ctx, const char *s) {
    if (ctx->puts) ctx->puts(s);
}

cy_bringup_result_t cy_bringup_run(cy_hpi_ctx_t *ctx,
                                   const cy_bringup_blobs_t *blobs,
                                   int stop_on_failure) {
    uint16_t hwrev = 0, cpu = 0, pwr = 0;
    uint16_t rb = 0;

    log_stage(ctx, "CY_STAGE0_FPGA_HPI_BRIDGE_START\n");
    cy_hpi_set_timing(ctx, CY_HPI_DEFAULT_ACCESS_CYCLES,
                      CY_HPI_DEFAULT_SAMPLE_OFFSET,
                      CY_HPI_DEFAULT_TURNAROUND_CYCLES, 1, 0);
    cy_hpi_dump_debug(ctx, "CY_STAGE0_DBG");
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
        if (stop_on_failure) return CY_BRINGUP_FAIL_REG_READ;
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
        if (stop_on_failure) return CY_BRINGUP_FAIL_RAM_RW;
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
        if (stop_on_failure) return CY_BRINGUP_FAIL_LCP_HANDSHAKE;
    } else {
        log_stage(ctx, "CY_STAGE4B_LCP_HANDSHAKE_PASS\n");
    }

    if (blobs && blobs->scan_image && blobs->scan_image_len) {
        cy_scan_stats_t stats;
        log_stage(ctx, "CY_STAGE5_SCAN_COPY_START\n");
        if (!cy_scan_execute_over_hpi(ctx, blobs->scan_image, blobs->scan_image_len, &stats, 0)) {
            log_stage(ctx, "CY_STAGE5_SCAN_COPY_FAIL\n");
            if (stop_on_failure) return CY_BRINGUP_FAIL_SCAN;
        }
        if (ctx->puts && ctx->puthex32) {
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
            if (stop_on_failure) return CY_BRINGUP_FAIL_LCP;
        }
        log_stage(ctx, "CY_STAGE6_LCP_CALL_PASS\n");
    } else {
        log_stage(ctx, "CY_STAGE6_LCP_CALL_SKIP\n");
    }

    log_stage(ctx, "CY_STAGE7_BIOS_INT_SKIP\n");
    return CY_BRINGUP_OK;
}
