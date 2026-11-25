CXX      ?= g++
CXXFLAGS ?= -O3 -std=c++20 -fPIC -pthread -Wall -Wextra
LDFLAGS  ?= -shared -pthread

TARGET   := libclockchecker.so
SRCS     := solver.cpp
HDRS     := clockchecker.hpp

EMCC     ?= em++
WASM_OUT := ../../webapp/clockchecker_wasm.js
WASM_FLAGS := -O3 -std=c++20 -DCLOCKCHECKER_SINGLE_THREADED -Wall -Wextra \
	-sMODULARIZE=1 -sEXPORT_ES6=1 -sEXPORT_NAME=createClockcheckerModule \
	-sSTACK_SIZE=4194304 -sALLOW_MEMORY_GROWTH=1 -sALLOW_TABLE_GROWTH=1 \
	-sEXPORTED_FUNCTIONS='["_solve_puzzle_cpp_stream","_solve_puzzle_cpp_mt","_get_serialized_puzzle_size","_get_serialized_solution_size","_malloc","_free"]' \
	-sEXPORTED_RUNTIME_METHODS='["HEAPU8","addFunction","removeFunction"]'

.PHONY: all debug wasm clean

all: $(TARGET)

$(TARGET): $(SRCS) $(HDRS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(SRCS) -o $(TARGET)

wasm: $(SRCS) $(HDRS)
	$(EMCC) $(WASM_FLAGS) $(SRCS) -o $(WASM_OUT)

debug: CXXFLAGS := -O0 -g -std=c++20 -fPIC -pthread -Wall -Wextra
debug: clean $(TARGET)

clean:
	rm -f $(TARGET) $(WASM_OUT) $(WASM_OUT:.js=.wasm)

