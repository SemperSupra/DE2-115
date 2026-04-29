#ifndef CY7C67200_LCP_H
#define CY7C67200_LCP_H

#include <stdint.h>
#include "cy7c67200_hpi.h"

int cy_lcp_wait_ack(cy_hpi_ctx_t *ctx, uint32_t timeout);
int cy_lcp_call_code(cy_hpi_ctx_t *ctx, uint16_t addr, uint32_t timeout);
int cy_lcp_jump_to_code(cy_hpi_ctx_t *ctx, uint16_t addr, uint32_t post_delay_ms);
int cy_lcp_exec_int_r0(cy_hpi_ctx_t *ctx, uint16_t int_num, uint16_t r0,
                       uint32_t timeout, const char *name);

#endif
