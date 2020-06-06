//#include <stdio.h>
#include <stdlib.h>
#include <zmq.hpp>
#include <iostream>
#include <sstream>
#include <valarray>

#include "midas.h"
#include "msystem.h"
#include "mfe.h"
#include "evutils.h"

//#define DEBUG

/*-- Globals -------------------------------------------------------*/

/* The frontend name (client name) as seen by other MIDAS clients   */
const char *frontend_name = "MegaManFE";
/* The frontend file name, don't change it */
const char *frontend_file_name = __FILE__;

/* frontend_loop is called periodically if this variable is TRUE    */
BOOL frontend_call_loop = FALSE;

/* a frontend status page is displayed with this frequency in ms */
INT display_period = 0;

/* maximum event size produced by this frontend */
INT max_event_size = 10000;

/* maximum event size for fragmented events (EQ_FRAGMENTED) */
INT max_event_size_frag = 5 * 1024 * 1024;

/* buffer size to hold events */
INT event_buffer_size = 100 * 10000;

#define NUM_THREADS	4

struct _pdata {
   int index;
   unsigned short int nmod;
   unsigned short int nsam;
};

struct _pdata pdata[NUM_THREADS];

zmq::context_t context(1);

/*-- Function declarations -----------------------------------------*/

INT trigger_thread(void *param);

/*-- Equipment list ------------------------------------------------*/

EQUIPMENT equipment[] = {

   {"MegampManager00-data",  /* equipment name */
    {1, 0,                   /* event ID, trigger mask */
     "SYSTEM",               /* event buffer */
     EQ_USER,                /* equipment type */
     0,                      /* event source (not used) */
     "MIDAS",                /* format */
     TRUE,                   /* enabled */
     RO_RUNNING,             /* read only when running */
     500,                    /* poll for 500ms */
     0,                      /* stop run after this event limit */
     0,                      /* number of sub events */
     0,                      /* don't log history */
     "", "", "",},
    NULL,                    /* readout routine */
    },

   {""}
};

/*-- Frontend Init -------------------------------------------------*/

INT frontend_init()
{
   /* for this demo, use two readout threads */
   for (int i=0 ; i<NUM_THREADS ; i++) {
      
      pdata[i].index = i;
      // read from ODB...
      pdata[i].nmod = 8;
      pdata[i].nsam = 5;
      //

      /* create a ring buffer for each thread */
      create_event_rb(i);
      
      /* create readout thread */
      ss_thread_create(trigger_thread, &pdata[i]);
   }
   
   return SUCCESS;
}

/*-- Frontend Exit -------------------------------------------------*/

INT frontend_exit()
{
   return SUCCESS;
}

/*-- Begin of Run --------------------------------------------------*/

INT begin_of_run(INT run_number, char *error)
{
   return SUCCESS;
}

/*-- End of Run ----------------------------------------------------*/

INT end_of_run(INT run_number, char *error)
{
   return SUCCESS;
}

/*-- Pause Run -----------------------------------------------------*/

INT pause_run(INT run_number, char *error)
{
   return SUCCESS;
}

/*-- Resume Run ----------------------------------------------------*/

INT resume_run(INT run_number, char *error)
{
   return SUCCESS;
}

/*-- Frontend Loop -------------------------------------------------*/

INT frontend_loop()
{
   /* if frontend_call_loop is true, this routine gets called when
      the frontend is idle or once between every event */
   return SUCCESS;
}

/*-- Trigger event routines ----------------------------------------*/

INT poll_event(INT source, INT count, BOOL test)
/* Polling is not used */
{
   return 0;
}

/*-- Interrupt configuration ---------------------------------------*/

INT interrupt_configure(INT cmd, INT source, POINTER_T adr)
/* Interrupts are not used */
{
   return SUCCESS;
}

/*-- Event readout -------------------------------------------------*/

INT trigger_thread(void *param)
{
   EVENT_HEADER *pevent;
   WORD *pdata, *pmegamp;
   int  index, status;
   unsigned short int nmod, nsam;
   INT rbh;

   struct _pdata *tdata = (struct _pdata *) param;

   zmq::socket_t s(context, zmq::socket_type::pull);
   s.connect("tcp://lxconga01.na.infn.it:5000");

   /* index of this thread */
   index = (int)tdata->index;
   /* number of Megamp modules */
   nmod = (unsigned short int)tdata->nmod;
   /* number of samples per channel */
   nsam = (unsigned short int)tdata->nsam;

   /* tell framework that we are alive */
   signal_readout_thread_active(index, TRUE);
   
   /* Initialize hardware here ... */
   printf("Start readout thread %d\n", index);
   
   /* Obtain ring buffer for inter-thread data exchange */
   rbh = get_event_rbh(index);
   
   while (is_readout_thread_enabled()) {
      
      /* obtain buffer space */
      status = rb_get_wp(rbh, (void **)&pevent, 0);
      if (!is_readout_thread_enabled())
         break;
      if (status == DB_TIMEOUT) {
         ss_sleep(10);
         continue;
      }
      if (status != DB_SUCCESS)
         break;
      
      /* check for new event (poll) */
      
      if (status) { // if event available, read it out
         
         if (!is_readout_thread_enabled())
            break;

	 zmq::message_t message{};
	 s.recv(message, zmq::recv_flags::none);

	 RawEvent event_raw(reinterpret_cast<unsigned short int*>(message.data()), message.size()/2);

	 // check event: size too short, EC mismatch, LEN error, CRC error

         bm_compose_event(pevent, 1, 0, 0, equipment[0].serial_number++);
         pdata = (WORD *)(pevent + 1);
         
         /* init bank structure */
         bk_init(pdata);
         
         // create a bank for each Megamp and fill each bank with channels and samples
	 unsigned int time = GetTime(event_raw);
	 for(int m=0; m<nmod; m++) {
	    std::stringstream bankname; 
	    bankname << "M00" << m;
	    bk_create(pdata, bankname.str().c_str(), TID_WORD, (void **)&pmegamp);
	    *pmegamp++ = GetEC(event_raw);

	    *pmegamp++ = (time & 0xFFFF0000) >> 16;
	    *pmegamp++ = (time & 0x0000FFFF);
	    *pmegamp++ = nmod;
	    *pmegamp++ = nsam;
	    for(int c=0; c<16; c++) {
	       *pmegamp++ = c;
	       std::vector<unsigned short int> chdata = GetChannelSamples(event_raw, m, c, nsam);
	       std::copy(begin(chdata), end(chdata), pmegamp);
	       pmegamp += chdata.size();
	    }
	    bk_close(pdata, pmegamp);
	 }

         pevent->data_size = bk_size(pdata);
         
         /* send event to ring buffer */
         rb_increment_wp(rbh, sizeof(EVENT_HEADER) + pevent->data_size);
      }
   }
   
   /* tell framework that we are finished */
   signal_readout_thread_active(index, FALSE);
   
   printf("Stop readout thread %d\n", index);

   return 0;
}
