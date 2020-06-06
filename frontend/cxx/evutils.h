#ifndef EVUTILS_H_
#define EVUTILS_H_

#include <valarray>
#include <vector>

typedef std::valarray<unsigned short int> RawEvent;

unsigned short int GetEC(RawEvent &event);
unsigned short int GetLEN(RawEvent &event);
unsigned short int GetCRC(RawEvent &event);
std::vector<unsigned short int> GetChannelSamples(RawEvent &ev, unsigned short int m, unsigned short int ch, unsigned short ns);
unsigned int GetTime(RawEvent &event);

unsigned short int UnmaskEC(unsigned short int word);
unsigned short int UnmaskLEN(unsigned short int word);
unsigned short int UnmaskCRC(unsigned short int word);

bool CheckEC(RawEvent &event);
bool CheckLEN(RawEvent &event);
bool CheckCRC(RawEvent &event);

#endif
