/**
/*
 * Copyright (c) 2026 Abhishek Singh (GitHub: Abhishek1033ubuntu)
 * Licensed under the Apache License, Version 2.0 (the "License-Software");
 * You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
 */ 
 * ============================================================================
 * RIM Security & Compression Engine (R-SCE) 12nm Companion ASIC Driver
 * ============================================================================
 * File: firmware/r_sce_dma_crypto_driver.c
 * License: Apache-2.0
 * Description:
 *   Low-level Linux/Android Kernel HAL driver for the custom 12nm R-SCE 
 *   Companion ASIC. Implements zero-copy DMA ring-buffer management,
 *   wire-speed AES-256-GCM hardware encryption, and inline real-time
 *   packet decompression (2.5+ GB/s throughput).
 * ============================================================================
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/io.h>
#include <linux/interrupt.h>
#include <linux/dma-mapping.h>
#include <linux/platform_device.h>
#include <linux/spinlock.h>
#include <linux/types.h>

/* --- R-SCE MMIO REGISTER MAP OFFSETS --- */
#define RSCE_REG_CTRL               0x0000 /* Control Register                    */
#define RSCE_REG_STATUS             0x0004 /* Hardware Status & Line State        */
#define RSCE_REG_IRQ_ENABLE         0x0008 /* Interrupt Mask Enable               */
#define RSCE_REG_IRQ_STATUS         0x000C /* Pending IRQ Clear-On-Write          */
#define RSCE_REG_DMA_RING_HEAD      0x0010 /* Host Ring Write Pointer (64-bit)    */
#define RSCE_REG_DMA_RING_TAIL      0x0018 /* ASIC Ring Read Pointer (64-bit)     */
#define RSCE_REG_RING_CAPACITY      0x0020 /* Max Ring Descriptors (Default: 256) */
#define RSCE_REG_CRYPTO_KEY_0       0x0030 /* AES-256 Key Word 0-7                */
#define RSCE_REG_COMPRESSION_CFG    0x0050 /* LZ4/Huffman Hard-wired Codec Control*/
#define RSCE_REG_PERF_CYCLE_CNT     0x0060 /* Hardware Clock Counter              */

/* --- CONTROL & STATUS BIT MASKS --- */
#define RSCE_CTRL_ENABLE            (1U << 0)
#define RSCE_CTRL_RESET             (1U << 1)
#define RSCE_CTRL_ENCRYPTION_BYPASS (1U << 2)
#define RSCE_CTRL_COMPRESSION_BYPASS(1U << 3)
#define RSCE_STATUS_IDLE            (1U << 0)
#define RSCE_STATUS_BUSY            (1U << 1)
#define RSCE_STATUS_ERROR           (1U << 31)

#define RSCE_RING_SIZE              256
#define RSCE_DMA_ALIGNMENT          64

/**
 * struct r_sce_dma_desc - Hardware Scatter-Gather Descriptor (64-byte Aligned)
 */
struct r_sce_dma_desc {
    u64 src_phys_addr;   /* Source buffer physical address            */
    u64 dst_phys_addr;   /* Destination buffer physical address       */
    u32 src_len;         /* Uncompressed / encrypted payload bytes    */
    u32 dst_len;         /* Allocated output buffer byte capacity    */
    u32 control_flags;   /* Bit 0: Encrypt, Bit 1: Decompress, Bit 2: IRQ */
    u32 tag_id;          /* Transaction ID for zero-copy DMA tracking */
    u64 reserved[3];     /* Padding to achieve 64-byte cache alignment */
} __packed __aligned(64);

/**
 * struct r_sce_device - Main Driver Context Structure
 */
struct r_sce_device {
    void __iomem *mmio_base;
    int irq;
    struct device *dev;
    
    /* DMA Ring Buffers */
    struct r_sce_dma_desc *ring_cpu;
    dma_addr_t ring_dma;
    u32 head;
    u32 tail;
    
    spinlock_t lock;
    u64 total_processed_bytes;
};

/* --- LOW-LEVEL MMIO ACCESSORS --- */
static inline u32 rsce_read32(struct r_sce_device *rsce, u32 reg) {
    return ioread32(rsce->mmio_base + reg);
}

static inline void rsce_write32(struct r_sce_device *rsce, u32 reg, u32 val) {
    iowrite32(val, rsce->mmio_base + reg);
}

static inline void rsce_write64(struct r_sce_device *rsce, u32 reg, u64 val) {
    iowrite32(lower_32_bits(val), rsce->mmio_base + reg);
    iowrite32(upper_32_bits(val), rsce->mmio_base + reg + 4);
}

/**
 * r_sce_hardware_reset() - Flushes hardware FIFOs and resets the state machine
 */
static int r_sce_hardware_reset(struct r_sce_device *rsce) {
    u32 status;
    int timeout = 1000;

    rsce_write32(rsce, RSCE_REG_CTRL, RSCE_CTRL_RESET);
    
    while (timeout--) {
        status = rsce_read32(rsce, RSCE_REG_STATUS);
        if (status & RSCE_STATUS_IDLE)
            return 0;
        cpu_relax();
    }
    
    dev_err(rsce->dev, "R-SCE Companion ASIC Hardware Reset Timeout!\n");
    return -ETIMEDOUT;
}

/**
 * r_sce_submit_dma_job() - Enqueues a packet for wire-speed crypto & compression
 */
int r_sce_submit_dma_job(struct r_sce_device *rsce, dma_addr_t src, dma_addr_t dst, 
                        u32 len, u32 flags, u32 tag) {
    unsigned long irq_flags;
    struct r_sce_dma_desc *desc;
    u32 next_head;

    spin_lock_irqsave(&rsce->lock, irq_flags);

    next_head = (rsce->head + 1) % RSCE_RING_SIZE;
    if (next_head == rsce->tail) {
        spin_unlock_irqrestore(&rsce->lock, irq_flags);
        return -EBUSY; /* DMA Ring Full */
    }

    desc = &rsce->ring_cpu[rsce->head];
    desc->src_phys_addr = src;
    desc->dst_phys_addr = dst;
    desc->src_len       = len;
    desc->dst_len       = len + 512; /* Max expansion buffer headroom */
    desc->control_flags = flags | 0x04; /* Enable completion IRQ */
    desc->tag_id        = tag;

    rsce->head = next_head;

    /* Notify ASIC Doorbell of new ring entry */
    wmb();
    rsce_write64(rsce, RSCE_REG_DMA_RING_HEAD, (u64)(rsce->ring_dma + (rsce->head * sizeof(*desc))));

    spin_unlock_irqrestore(&rsce->lock, irq_flags);
    return 0;
}
EXPORTS_SYMBOL(r_sce_submit_dma_job);

/**
 * r_sce_irq_handler() - Low-latency Interrupt Service Routine
 */
static irqreturn_t r_sce_irq_handler(int irq, void *dev_id) {
    struct r_sce_device *rsce = (struct r_sce_device *)dev_id;
    u32 irq_stat = rsce_read32(rsce, RSCE_REG_IRQ_STATUS);
    
    if (!irq_stat)
        return IRQ_NONE;

    /* Acknowledge pending IRQs */
    rsce_write32(rsce, RSCE_REG_IRQ_STATUS, irq_stat);

    if (irq_stat & 0x01) { /* DMA Ring Completion Interrupt */
        spin_lock(&rsce->lock);
        u64 tail_ptr = ioread32(rsce->mmio_base + RSCE_REG_DMA_RING_TAIL);
        rsce->tail = (tail_ptr - rsce->ring_dma) / sizeof(struct r_sce_dma_desc);
        spin_unlock(&rsce->lock);
    }

    return IRQ_HANDLED;
}

/**
 * r_sce_probe() - Kernel PCI/Platform Device Probe Initialization
 */
static int r_sce_probe(struct platform_device *pdev) {
    struct r_sce_device *rsce;
    struct resource *res;
    int ret;

    rsce = devm_kzalloc(&pdev->dev, sizeof(*rsce), GFP_KERNEL);
    if (!rsce)
        return -ENOMEM;

    rsce->dev = &pdev->dev;
    spin_lock_init(&rsce->lock);

    res = platform_get_resource(pdev, IORESOURCE_MEM, 0);
    rsce->mmio_base = devm_ioremap_resource(&pdev->dev, res);
    if (IS_ERR(rsce->mmio_base))
        return PTR_ERR(rsce->mmio_base);

    rsce->irq = platform_get_irq(pdev, 0);
    if (rsce->irq < 0)
        return rsce->irq;

    /* Allocate Coherent DMA Ring Memory */
    rsce->ring_cpu = dmam_alloc_coherent(&pdev->dev, 
                                        RSCE_RING_SIZE * sizeof(struct r_sce_dma_desc),
                                        &rsce->ring_dma, GFP_KERNEL);
    if (!rsce->ring_cpu)
        return -ENOMEM;

    ret = devm_request_irq(&pdev->dev, rsce->irq, r_sce_irq_handler, 0, "r_sce_asic", rsce);
    if (ret) {
        dev_err(&pdev->dev, "Failed to request IRQ line %d\n", rsce->irq);
        return ret;
    }

    /* Initialize Hardware ASIC Registers */
    r_sce_hardware_reset(rsce);
    rsce_write32(rsce, RSCE_REG_RING_CAPACITY, RSCE_RING_SIZE);
    rsce_write32(rsce, RSCE_REG_IRQ_ENABLE, 0x01); /* Enable DMA completion IRQ */
    rsce_write32(rsce, RSCE_REG_CTRL, RSCE_CTRL_ENABLE);

    platform_set_drvdata(pdev, rsce);
    dev_info(&pdev->dev, "R-SCE 12nm Companion ASIC Initialized (Base MMIO: %pa, IRQ: %d)\n",
             &res->start, rsce->irq);

    return 0;
}

static int r_sce_remove(struct platform_device *pdev) {
    struct r_sce_device *rsce = platform_get_drvdata(pdev);
    rsce_write32(rsce, RSCE_REG_CTRL, 0); /* Disable ASIC */
    return 0;
}

static const struct of_device_id r_sce_of_match[] = {
    { .compatible = "rim,r-sce-12nm-asic", },
    { /* Sentinel */ }
};
MODULE_DEVICE_TABLE(of, r_sce_of_match);

static struct platform_driver r_sce_driver = {
    .probe  = r_sce_probe,
    .remove = r_sce_remove,
    .driver = {
        .name           = "r_sce_12nm_asic",
        .of_match_table = r_sce_of_match,
    },
};

module_platform_driver(r_sce_driver);

MODULE_AUTHOR("Abhishek Singh <abhishek1033ubuntu>");
MODULE_DESCRIPTION("RIM R-SCE 12nm Companion ASIC Low-Level Driver");
MODULE_LICENSE("GPL v2");
