CC=clang
CFLAGS=-g -Wall -Wextra
SRCS=$(wildcard *.c)
OBJS=$(SRCS:.c=.o)
TARGET=compile

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)
