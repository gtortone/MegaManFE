ifndef MIDASSYS
missmidas::
	@echo "...";
	@echo "Missing definition of environment variable 'MIDASSYS' !";
	@echo "...";
endif

INC_DIR   = $(MIDASSYS)/include
LIB_DIR   = $(MIDASSYS)/lib

CC = gcc
CXX = g++
OSFLAGS = -DOS_LINUX -Dextname
CFLAGS = -O2 -Wall -I$(INC_DIR) 
LIB = $(LIB_DIR)/libmidas.a
LIBS = -lm -lz -lutil -lpthread -lrt -lzmq

UFE = femegaman

all: $(UFE)

$(UFE): $(LIB) $(LIB_DIR)/mfe.o $(UFE).o evutils.o register.o
	$(CXX) $(CFLAGS) $(OSFLAGS) -o $(UFE) $(UFE).o $(LIB_DIR)/mfe.o evutils.o register.o $(LIB) $(LIBS)
	strip $(UFE)

%.o: %.cxx
	$(CXX) $(USERFLAGS) $(CFLAGS) $(OSFLAGS) -o $@ -c $<

clean::
	rm -f *.o *~ \#* $(UFE)

