#include "evutils.h"
#include <stdint.h>

unsigned short int GetEC(RawEvent &event) {
   return(UnmaskEC(event[1]));
}

unsigned short int GetLEN(RawEvent &event) {
   return(UnmaskLEN(event[event.size() - 2]));
}

unsigned short int GetCRC(RawEvent &event) {
   return(UnmaskCRC(event[event.size() - 1]));
}

std::vector<unsigned short int> GetChannelSamples(RawEvent &ev, unsigned short int m, unsigned short int ch, unsigned short ns) {
   std::vector<unsigned short int> chdata;
   int offset = 4;
   int start = m*(32+2+(ns*32)) + ch*(ns+1) + offset;
   int end = start + ns;
   for(int i=start; i<end; i++)
      chdata.push_back(ev[i]);
   return(chdata);
}

unsigned int GetTime(RawEvent &event) {
   int msb = event[event.size() - 4] << 16;
   int lsb = event[event.size() - 3] << 1;
   return (msb + lsb) >> 1;
}

unsigned short int UnmaskEC(unsigned short int word) {
   return (word & 0x0FFF);
}

unsigned short int UnmaskLEN(unsigned short int word) {
   return (word & 0x0FFF);
}

unsigned short int UnmaskCRC(unsigned short int word) {
   return (word & 0x00FF);
}

bool CheckEC(RawEvent &event, unsigned short ns) {
   uint16_t i = 1;
   uint16_t readec = UnmaskEC(event[i]);
   int step = 2 + 32 + (32 * ns);
   while (i < event.size()) {
      if(UnmaskEC(event[i]) != readec) {
         return false;
      }
      i += step;
   }
   return true;
}

bool CheckLEN(RawEvent &event) {
   uint16_t evlen = GetLEN(event);
   int length = event.size() + 1;
   return (evlen == length);
}

bool CheckCRC(RawEvent &event) {
   uint16_t evcrc = GetCRC(event);
   int crc = 0;
   for(uint16_t  i=0; i<event.size()-1; i++) {
      uint8_t msb = (event[i] & 0xFF00) >> 8;
      uint8_t lsb = (event[i] & 0x00FF);
      crc = (crc ^ (msb ^ lsb));
   }
   uint8_t crc8 = crc & 0x00FF;
   return (evcrc == crc8);
}
