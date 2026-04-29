#include "cy7c67200_lcp.h"
#include "cy7c67200_regs.h"

int cy_lcp_wait_ack(cy_hpi_ctx_t *ctx, uint32_t timeout) {
    while (timeout--) {
        uint16_t st = cy_hpi_status_read(ctx);
        if (st & CY_HPI_STATUS_MAILBOX_OUT) {
            uint16_t mb = cy_hpi_mailbox_read(ctx);
            if (mb == CY_COMM_ACK) return 1;
            if (mb == CY_COMM_NAK) return 0;
        }
    }
    return 0;
}

int cy_lcp_call_code(cy_hpi_ctx_t *ctx, uint16_t addr, uint32_t timeout) {
    cy_hpi_write16(ctx, CY_COMM_CODE_ADDR, addr);
    cy_hpi_mailbox_write(ctx, CY_COMM_CALL_CODE);
    return cy_lcp_wait_ack(ctx, timeout);
}

int cy_lcp_jump_to_code(cy_hpi_ctx_t *ctx, uint16_t addr, uint32_t post_delay_ms) {
    cy_hpi_write16(ctx, CY_COMM_CODE_ADDR, addr);
    cy_hpi_mailbox_write(ctx, CY_COMM_JUMP2CODE);
    if (ctx->sleep_ms) ctx->sleep_ms(post_delay_ms);
    return 1;
}

int cy_lcp_exec_int_r0(cy_hpi_ctx_t *ctx, uint16_t int_num, uint16_t r0,
                       uint32_t timeout, const char *name) {
    cy_hpi_write16(ctx, CY_COMM_INT_NUM, int_num);
    cy_hpi_write16(ctx, CY_COMM_R0, r0);
    cy_hpi_mailbox_write(ctx, CY_COMM_EXEC_INT);

    if (cy_lcp_wait_ack(ctx, timeout)) {
        if (ctx->puts) {
            ctx->puts(name ? name : "LCP_INT");
            ctx->puts(" ACK\n");
        }
        return 1;
    }

    if (ctx->puts && ctx->puthex16) {
        ctx->puts(name ? name : "LCP_INT");
        ctx->puts(" NOACK mb=");
        ctx->puthex16(cy_hpi_mailbox_read(ctx));
        ctx->puts(" st=");
        ctx->puthex16(cy_hpi_status_read(ctx));
        ctx->puts("\n");
    }
    return 0;
}
