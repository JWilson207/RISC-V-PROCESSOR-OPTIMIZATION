# Makefile for RISC-V BOOM Benchmarks
# Compiles C code to RISC-V binaries for testing different cache configurations

# RISC-V toolchain
RISCV_PREFIX = riscv64-unknown-elf-
CC = $(RISCV_PREFIX)gcc
OBJDUMP = $(RISCV_PREFIX)objdump
OBJCOPY = $(RISCV_PREFIX)objcopy

# Directories
SRC_DIR = benchmarks
BUILD_DIR = build
RISCV_DIR = riscv_bins

# Compilation flags
CFLAGS = -march=rv64g -mabi=lp64d -static -mcmodel=medany
CFLAGS += -O2 -fno-common
CFLAGS += -I$(SRC_DIR)

# Linker flags
LDFLAGS = -static -lm -lc -lgcc

# Benchmarks
BENCHMARKS = multiplication qsort dhrystone aes convolution sha256

# All targets
all: $(BENCHMARKS)

# Create directories
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(RISCV_DIR):
	mkdir -p $(RISCV_DIR)

# Multiplication benchmark
multiplication: $(BUILD_DIR) $(RISCV_DIR)
	$(CC) $(CFLAGS) $(SRC_DIR)/multiplication.c -o $(BUILD_DIR)/multiplication.elf $(LDFLAGS)
	$(OBJCOPY) -O binary $(BUILD_DIR)/multiplication.elf $(RISCV_DIR)/multiplication.riscv
	$(OBJDUMP) -D $(BUILD_DIR)/multiplication.elf > $(BUILD_DIR)/multiplication.dump
	@echo "Built: multiplication.riscv"

# QSort benchmark
qsort: $(BUILD_DIR) $(RISCV_DIR)
	$(CC) $(CFLAGS) $(SRC_DIR)/qsort.c -o $(BUILD_DIR)/qsort.elf $(LDFLAGS)
	$(OBJCOPY) -O binary $(BUILD_DIR)/qsort.elf $(RISCV_DIR)/qsort.riscv
	$(OBJDUMP) -D $(BUILD_DIR)/qsort.elf > $(BUILD_DIR)/qsort.dump
	@echo "Built: qsort.riscv"

# Dhrystone benchmark
dhrystone: $(BUILD_DIR) $(RISCV_DIR)
	$(CC) $(CFLAGS) $(SRC_DIR)/dhrystone.c -o $(BUILD_DIR)/dhrystone.elf $(LDFLAGS)
	$(OBJCOPY) -O binary $(BUILD_DIR)/dhrystone.elf $(RISCV_DIR)/dhrystone.riscv
	$(OBJDUMP) -D $(BUILD_DIR)/dhrystone.elf > $(BUILD_DIR)/dhrystone.dump
	@echo "Built: dhrystone.riscv"

# AES benchmark
aes: $(BUILD_DIR) $(RISCV_DIR)
	$(CC) $(CFLAGS) $(SRC_DIR)/aes.c -o $(BUILD_DIR)/aes.elf $(LDFLAGS)
	$(OBJCOPY) -O binary $(BUILD_DIR)/aes.elf $(RISCV_DIR)/aes.riscv
	$(OBJDUMP) -D $(BUILD_DIR)/aes.elf > $(BUILD_DIR)/aes.dump
	@echo "Built: aes.riscv"

# Convolution benchmark
convolution: $(BUILD_DIR) $(RISCV_DIR)
	$(CC) $(CFLAGS) $(SRC_DIR)/convolution.c -o $(BUILD_DIR)/convolution.elf $(LDFLAGS)
	$(OBJCOPY) -O binary $(BUILD_DIR)/convolution.elf $(RISCV_DIR)/convolution.riscv
	$(OBJDUMP) -D $(BUILD_DIR)/convolution.elf > $(BUILD_DIR)/convolution.dump
	@echo "Built: convolution.riscv"

# SHA256 benchmark
sha256: $(BUILD_DIR) $(RISCV_DIR)
	$(CC) $(CFLAGS) $(SRC_DIR)/sha256.c -o $(BUILD_DIR)/sha256.elf $(LDFLAGS)
	$(OBJCOPY) -O binary $(BUILD_DIR)/sha256.elf $(RISCV_DIR)/sha256.riscv
	$(OBJDUMP) -D $(BUILD_DIR)/sha256.elf > $(BUILD_DIR)/sha256.dump
	@echo "Built: sha256.riscv"

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(RISCV_DIR)

# Show all built binaries
list:
	@echo "Built RISC-V binaries:"
	@ls -lh $(RISCV_DIR)/*.riscv 2>/dev/null || echo "No binaries found. Run 'make all' first."

# Check source files
check:
	@echo "Checking for source files in $(SRC_DIR)/:"
	@ls -1 $(SRC_DIR)/*.c 2>/dev/null || echo "No .c files found!"
	@echo ""
	@ls -1 $(SRC_DIR)/*.h 2>/dev/null || echo "No .h files found!"

.PHONY: all clean list check multiplication qsort dhrystone aes convolution sha256