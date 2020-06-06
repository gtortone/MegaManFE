#include "evutils.h"

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

bool CheckEC(RawEvent &event) {
}

bool CheckLEN(RawEvent &event) {
}

bool CheckCRC(RawEvent &event) {
}
