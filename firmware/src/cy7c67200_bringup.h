#ifndef CY7C67200_BRINGUP_H
#define CY7C67200_BRINGUP_H

#include <stdint.h>
#include "cy7c67200_hpi.h"

typedef enum cy_bringup_result {
    CY_BRINGUP_OK = 0,
    CY_BRINGUP_FAIL_HW_LOOPBACK = 1,
    CY_BRINGUP_FAIL_REG_READ = 2,
    CY_BRINGUP_FAIL_RAM_RW = 3,
    CY_BRINGUP_FAIL_LCP_HANDSHAKE = 4,
    CY_BRINGUP_FAIL_SCAN = 5,
    CY_BRINGUP_FAIL_LCP = 6,
    CY_BRINGUP_FAIL_BIOS_INT = 7
} cy_bringup_result_t;

typedef struct cy_bringup_blobs {
    const uint8_t *scan_image;
    uint32_t scan_image_len;
    uint16_t lcp_probe_call_addr;
} cy_bringup_blobs_t;

#define CY_BRINGUP_STOP_ON_FAILURE 1
#define CY_BRINGUP_CONTINUE_ON_FAILURE 0

cy_bringup_result_t cy_bringup_run(cy_hpi_ctx_t *ctx,
                                   const cy_bringup_blobs_t *blobs,
                                   int stop_on_failure);

#endif
