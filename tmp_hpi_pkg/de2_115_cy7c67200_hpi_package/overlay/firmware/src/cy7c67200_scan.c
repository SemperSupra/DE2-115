#include "cy7c67200_scan.h"
#include "cy7c67200_regs.h"
#include "cy7c67200_lcp.h"

static uint16_t rd16le(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}

int cy_scan_execute_over_hpi(cy_hpi_ctx_t *ctx, const uint8_t *image, uint32_t len,
                             cy_scan_stats_t *stats, int execute_control_records) {
    uint32_t pos = 0;

    if (stats) {
        stats->records = 0;
        stats->copy_records = 0;
        stats->call_records = 0;
        stats->jump_records = 0;
        stats->int_records = 0;
        stats->bytes_copied = 0;
        stats->malformed_records = 0;
    }

    while (pos + 5u <= len) {
        uint16_t sig = rd16le(&image[pos]);
        if (sig != CY_SCAN_SIGNATURE) break;

        uint16_t rlen = rd16le(&image[pos + 2u]);
        uint8_t op = image[pos + 4u];
        uint32_t data_pos = pos + 5u;
        uint32_t next_pos = pos + 5u + (uint32_t)rlen;

        if (next_pos > len || rlen == 0u) {
            if (stats) stats->malformed_records++;
            return 0;
        }

        if (stats) stats->records++;

        if (op == CY_SCAN_OPCODE_COPY) {
            if (rlen < 2u) {
                if (stats) stats->malformed_records++;
                return 0;
            }
            uint16_t addr = rd16le(&image[data_pos]);
            uint16_t payload_len = (uint16_t)(rlen - 2u);
            cy_hpi_write_block(ctx, addr, &image[data_pos + 2u], payload_len);
            if (stats) {
                stats->copy_records++;
                stats->bytes_copied += payload_len;
            }
        } else if (op == CY_SCAN_OPCODE_CALL) {
            if (rlen < 2u) {
                if (stats) stats->malformed_records++;
                return 0;
            }
            uint16_t addr = rd16le(&image[data_pos]);
            if (stats) stats->call_records++;
            if (execute_control_records && !cy_lcp_call_code(ctx, addr, 1000000u)) return 0;
        } else if (op == CY_SCAN_OPCODE_JUMP) {
            if (rlen < 2u) {
                if (stats) stats->malformed_records++;
                return 0;
            }
            uint16_t addr = rd16le(&image[data_pos]);
            if (stats) stats->jump_records++;
            if (execute_control_records) cy_lcp_jump_to_code(ctx, addr, 50u);
        } else if (op == CY_SCAN_OPCODE_INT) {
            if (stats) stats->int_records++;
            if (execute_control_records) return 0;
        } else {
            if (stats) stats->malformed_records++;
            return 0;
        }

        pos = next_pos;
    }

    return 1;
}
