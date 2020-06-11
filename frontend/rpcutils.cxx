#include "rpcutils.h"

std::string getProxyStatus(std::string host) {

   std::string const serverUrl("http://" + host + ":9001/RPC2");
   xmlrpc_c::carriageParm_curl0 myCarriageParm(serverUrl);
   myCarriageParm.setUser("midas", "m1d4s");
   myCarriageParm.allowAuthBasic();

   xmlrpc_c::clientXmlTransport_curl myTransport;
   xmlrpc_c::client_xml myClient(&myTransport);
   std::string const infoMethod("supervisor.getProcessInfo");

   xmlrpc_c::paramList procParams;
   procParams.add(xmlrpc_c::value_string("megaman-usb-proxy"));
          
   xmlrpc_c::rpcPtr procinfo(infoMethod, procParams);

   procinfo->call(&myClient, &myCarriageParm);
   xmlrpc_c::value result = procinfo->getResult();
   std::map<std::string, xmlrpc_c::value> cs = xmlrpc_c::value_struct(result);

   return(xmlrpc_c::value_string(cs["statename"]));
}


void sendProxyStart(std::string host) {

   std::string const serverUrl("http://" + host + ":9001/RPC2");
   xmlrpc_c::carriageParm_curl0 myCarriageParm(serverUrl);
   myCarriageParm.setUser("midas", "m1d4s");
   myCarriageParm.allowAuthBasic();

   xmlrpc_c::clientXmlTransport_curl myTransport;
   xmlrpc_c::client_xml myClient(&myTransport);
   std::string const startMethod("supervisor.startProcess");

   xmlrpc_c::paramList procParams;
   procParams.add(xmlrpc_c::value_string("megaman-usb-proxy"));
          
   xmlrpc_c::rpcPtr procstart(startMethod, procParams);

   procstart->call(&myClient, &myCarriageParm);
}
