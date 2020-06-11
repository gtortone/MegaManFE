#ifndef _RPCUTILS_H_
#define _RPCUTILS_H_

#include <string>
#include <xmlrpc-c/girerr.hpp>
#include <xmlrpc-c/client_transport.hpp>
#include <xmlrpc-c/client.hpp>

std::string getProxyStatus(std::string);
void sendProxyStart(std::string);

#endif
