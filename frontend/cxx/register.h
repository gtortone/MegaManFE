#ifndef _REGISTER_H_
#define _REGISTER_H_

#define BOR    0b0001  // begin of run
#define SOF    0b0010  // start of frontend
#define SCLR   0b0100  // register self clear
#define SCAN   0b1000  // register to read periodically

#define SETTINGS_TREE   std::string("Settings")
#define VARIABLES_TREE  std::string("Variables")

typedef struct reg {
   std::string subtree;
   std::string label;
   uint16_t addr;
   uint8_t flags;
} Register;

uint16_t GetRegAddress(std::string);
std::vector<Register> GetRegs(const uint8_t flag = 0);
std::vector<Register> GetCommitRegs(void);

#endif
