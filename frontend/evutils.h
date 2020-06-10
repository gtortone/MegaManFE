#ifndef EVUTILS_H_
#define EVUTILS_H_

#include <valarray>
#include <vector>

typedef std::valarray<unsigned short int> RawEvent;

unsigned short int GetEC(RawEvent &);
unsigned short int GetLEN(RawEvent &);
unsigned short int GetCRC(RawEvent &);
std::vector<unsigned short int> GetChannelSamples(RawEvent &, unsigned short int, unsigned short int, unsigned short);
unsigned int GetTime(RawEvent &event);

unsigned short int UnmaskEC(unsigned short int);
unsigned short int UnmaskLEN(unsigned short int);
unsigned short int UnmaskCRC(unsigned short int);

bool CheckEC(RawEvent &, unsigned short);
bool CheckLEN(RawEvent &);
bool CheckCRC(RawEvent &);

#endif
