# --- Utilities Names ---
SERVER_PARSER      := server-parser
SNI_SENDER    := quic-sni-sender

# --- Docker Images and Rust Target ---
GO_IMG      ?= golang:1.22-bookworm
RUST_IMG    ?= rust:1.82-bookworm
RUST_TRIPLE := x86_64-unknown-linux-gnu

# --- Build Configuration ---
BUILD_DIR   ?= tools
TARGET_OS   ?= linux
TARGET_ARCH ?= amd64

PAYLOADS_DIR := ../experiments/what-triggers-blocking/payloads

# --- Deployment Configuration ---
# The following variables can be overridden from the command line.
# Example: make deploy SERVER_HOST=your-server.com CLIENT_USER=your-user
SERVER_USER ?= ubuntu
SERVER_HOST ?= usenix-ae-us
SERVER_SSH_KEY ?=

CLIENT_USER ?= ubuntu
CLIENT_HOST ?= usenix-ae-cn
CLIENT_SSH_KEY ?=

REMOTE_DIR  ?= ~/
RSYNC_OPTS  ?= -avz --progress

# --- Internal Variables ---
BIN_GO      := $(BUILD_DIR)/$(SERVER_PARSER)
BIN_RUST    := $(BUILD_DIR)/$(SNI_SENDER)
GO_ENV      := CGO_ENABLED=1 GOOS=$(TARGET_OS) GOARCH=$(TARGET_ARCH)

# Conditionally set SSH options for rsync if a key is provided
SERVER_SSH_OPT :=
ifneq ($(SERVER_SSH_KEY),)
	SERVER_SSH_OPT := -e "ssh -i $(SERVER_SSH_KEY)"
endif

CLIENT_SSH_OPT :=
ifneq ($(CLIENT_SSH_KEY),)
	CLIENT_SSH_OPT := -e "ssh -i $(CLIENT_SSH_KEY)"
endif


.PHONY: all build build_parser build_sender deploy clean help

all: build deploy

build: | $(BUILD_DIR) build_sender build_parser

## Build the quic-sni-sender
build_sender: $(BIN_RUST)
$(BIN_RUST): | $(BUILD_DIR)
	docker run --rm \
		-v $(CURDIR):/src:Z \
		-w /src/$(SNI_SENDER) \
		--platform $(TARGET_OS)/$(TARGET_ARCH) \
		$(RUST_IMG) \
		bash -c 'rustup target add $(RUST_TRIPLE) && \
		apt-get -qq update && \
		apt-get -qq install -y cmake build-essential pkg-config libssl-dev clang libclang-dev && \
		cargo build --release --target $(RUST_TRIPLE) && \
		cp target/$(RUST_TRIPLE)/release/$(SNI_SENDER) ./';
	cp $(SNI_SENDER)/$(SNI_SENDER) $(BUILD_DIR)/

## Build the server-parser
build_parser: $(BIN_GO)
$(BIN_GO): | $(BUILD_DIR)
	docker run --rm \
		-v $(CURDIR):/src:Z \
		-w /src/$(SERVER_PARSER) \
		--platform $(TARGET_OS)/$(TARGET_ARCH) \
		$(GO_IMG) \
		bash -c 'apt-get -qq update && \
				 apt-get -qq install -y libpcap-dev && \
				 $(GO_ENV) go build -o /src/$@ .';

$(BUILD_DIR):
	@mkdir -p $@

deploy: build
	rsync $(RSYNC_OPTS) $(SERVER_SSH_OPT) $(BUILD_DIR)/ $(SERVER_USER)@$(SERVER_HOST):$(REMOTE_DIR)/
	rsync $(RSYNC_OPTS) $(CLIENT_SSH_OPT) $(BUILD_DIR)/ $(CLIENT_USER)@$(CLIENT_HOST):$(REMOTE_DIR)/
	rsync $(RSYNC_OPTS) $(CLIENT_SSH_OPT) $(PAYLOADS_DIR)/ $(CLIENT_USER)@$(CLIENT_HOST):$(REMOTE_DIR)/payloads

	# Add an iptables rule on the server to drop outgoing ICMP packets to the client.
	# The command checks if the rule exists before adding it to avoid duplicates.
	@if [ -z "$(CLIENT_HOST)" ]; then \
		echo "Error: CLIENT_HOST could not be determined from CLIENT_HOST."; \
		exit 1; \
	fi
	@echo "Configuring firewall on server ($(SERVER_HOST))..."
	ssh -i $(SERVER_SSH_KEY) $(SERVER_USER)@$(SERVER_HOST) '\
		if ! sudo iptables -C OUTPUT -p icmp -d $(CLIENT_HOST) -j DROP 2>/dev/null; then \
			sudo iptables -A OUTPUT -p icmp -d $(CLIENT_HOST) -j DROP; \
			echo "Firewall rule added to block ICMP to $(CLIENT_HOST)."; \
		else \
			echo "Firewall rule to block ICMP to $(CLIENT_HOST) already exists."; \
		fi'

clean:
	rm -rf $(BUILD_DIR)

help:
	@echo "Usage: make [TARGET] [VARIABLE=VALUE...]"
	@echo ""
	@echo "Targets:"
	@echo "  all           Build and deploy all binaries."
	@echo "  build         Build all binaries."
	@echo "  deploy        Deploy binaries to server and client hosts."
	@echo "  clean         Remove build artifacts."
	@echo "  help          Display this help message."
	@echo ""
	@echo "Configurable Deployment Variables:"
	@echo "  SERVER_HOST    Hostname/IP of the deployment server (default: usenix-ae-us)"
	@echo "  SERVER_USER    Username for the deployment server (default: ubuntu)"
	@echo "  SERVER_SSH_KEY Path to the SSH private key for the server (optional)"
	@echo "  CLIENT_HOST    Hostname/IP of the deployment client (default: usenix-ae-cn)"
	@echo "  CLIENT_USER    Username for the deployment client (default: ubuntu)"
	@echo "  CLIENT_SSH_KEY Path to the SSH private key for the client (optional)"


.DELETE_ON_ERROR: