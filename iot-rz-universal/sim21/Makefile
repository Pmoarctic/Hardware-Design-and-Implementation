CC=clang
CFLAGS=-g -Wall -Wextra
SRCS=s21.c io.c load.c mon.c
OBJS=$(SRCS:.c=.o)
TARGET=sim21

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $(OBJS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJS) $(TARGET)
