CC=clang
CFLAGS=-g -Wall -Wextra
SRCS=as21.c hash.c
OBJS=$(SRCS:.c=.o)
TARGET=as21

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)

