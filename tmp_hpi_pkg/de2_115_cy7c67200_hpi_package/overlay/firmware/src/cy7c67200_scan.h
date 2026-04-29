#ifndef CY7C67200_SCAN_H
#define CY7C67200_SCAN_H

#include <stdint.h>
#include <stddef.h>
#include "cy7c67200_hpi.h"

typedef struct cy_scan_stats {
    uint32_t records;
    uint32_t copy_records;
    uint32_t call_records;
    uint32_t jump_records;
    uint32_t int_records;
    uint32_t bytes_copied;
    uint32_t malformed_records;
} cy_scan_stats_t;

int cy_scan_execute_over_hpi(cy_hpi_ctx_t *ctx, const uint8_t *image, uint32_t len,
                             cy_scan_stats_t *stats, int execute_control_records);

#endif
