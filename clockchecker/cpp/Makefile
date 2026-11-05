CXX      ?= g++
CXXFLAGS ?= -O3 -std=c++20 -fPIC -Wall -Wextra
LDFLAGS  ?= -shared

TARGET   := libclockchecker.so
SRCS     := solver.cpp
HDRS     := clockchecker.hpp

.PHONY: all debug clean

all: $(TARGET)

$(TARGET): $(SRCS) $(HDRS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(SRCS) -o $(TARGET)

debug: CXXFLAGS := -O0 -g -std=c++20 -fPIC -Wall -Wextra
debug: clean $(TARGET)

clean:
	rm -f $(TARGET)

