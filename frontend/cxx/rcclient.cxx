#include <iostream>
#include <xmlrpc-c/girerr.hpp>
#include <xmlrpc-c/base.hpp>
#include <xmlrpc-c/client_simple.hpp>

#include "rcclient.h"

uint16_t RuncontrolClient::readReg(uint16_t addr) {

   std::string methodName("readreg");
   int reply;

   xmlrpc_c::clientSimple client;
   xmlrpc_c::value result;
       
   client.call(serverUrl, methodName, "i", &result, addr);

   reply = xmlrpc_c::value_int(result);

   return(reply);
}

void RuncontrolClient::writeReg(uint16_t addr, uint16_t value) {

   std::string methodName("writereg");

   xmlrpc_c::clientSimple client;
   xmlrpc_c::value result;

   client.call(serverUrl, methodName, "ii", &result, addr, value);
}
