
CXX = g++
CFLAGS = -O3 -Wall -std=c++11
LIBS = -lm -lutil -lpthread -lrt -lusb-1.0 -lzmq

all: feproxy 

feproxy:  $(LIB) feproxy.o 
	$(CXX) $(CFLAGS) -o feproxy feproxy.o $(LIBS)
	strip feproxy 

feproxy.o:	feproxy.cxx
	$(CXX) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o *~ \#* feproxy

