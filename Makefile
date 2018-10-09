PROJECT := lookout-sdk

# Including ci Makefile
CI_REPOSITORY ?= https://github.com/src-d/ci.git
CI_BRANCH ?= v1
CI_PATH ?= .ci
MAKEFILE := $(CI_PATH)/Makefile.main
$(MAKEFILE):
	git clone --quiet --depth 1 -b $(CI_BRANCH) $(CI_REPOSITORY) $(CI_PATH);
-include $(MAKEFILE)


# Generate go+python code from .proto files
.PHONY: check-protoc
check-protoc:
		./_tools/install-protoc-maybe.sh
.PHONY: protogen
protogen: check-protoc
		$(GOCMD) get github.com/gogo/protobuf/protoc-gen-gogofaster
		./_tools/protogen_golang.sh
		pip3 install --user grpcio_tools==1.13.0
		./_tools/protogen_python.sh
