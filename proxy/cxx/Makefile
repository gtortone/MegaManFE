
CXX = g++
CFLAGS = -O3 -Wall -std=c++11
LIBS = -lm -lutil -lpthread -lrt -lusb-1.0 -lzmq -lxmlrpc_server++ -lxmlrpc++ -lxmlrpc_server_abyss++

all: feproxy 

feproxy:  $(LIB) feproxy.o runcontrol.o
	$(CXX) $(CFLAGS) -o feproxy feproxy.o runcontrol.o $(LIBS)
	strip feproxy 

%.o: %.cxx
	$(CXX) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o *~ \#* feproxy

