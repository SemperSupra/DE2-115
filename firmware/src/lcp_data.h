/* Automatically parsed from Linux cy7c67x00.bin */
#ifndef LCP_DATA_H
#define LCP_DATA_H

#include <stdint.h>

struct lcp_record {
    uint16_t addr;
    uint16_t len;
    const uint16_t *data;
};

#define LCP_RECORD_COUNT 0

static const struct lcp_record lcp_records[] = {
};

#endif
