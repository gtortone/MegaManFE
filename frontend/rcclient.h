#ifndef _RUNCONTROLCLIENT_H_
#define _RUNCONTROLCLIENT_H_

#include <string>

class RuncontrolClient {

   private:
      std::string serverUrl;

   public:
      RuncontrolClient(std::string url) : serverUrl(url) {}
      RuncontrolClient(void) {};

      void setHost(std::string);
      uint16_t readReg(uint16_t);
      void writeReg(uint16_t, uint16_t);
};

#endif
