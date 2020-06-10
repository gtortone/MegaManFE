#ifndef _RUNCONTROLCLIENT_H_
#define _RUNCONTROLCLIENT_H_

#include <string>

class RuncontrolClient {

   private:
      std::string serverUrl;

   public:
      RuncontrolClient(std::string url) : serverUrl(url) {}

      uint16_t readReg(uint16_t addr);
      void writeReg(uint16_t addr, uint16_t value);
};

#endif
