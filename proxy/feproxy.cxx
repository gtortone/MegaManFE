#include <iostream>
#include <stdio.h>
#include <stdexcept>
#include <libusb-1.0/libusb.h>
#include <zmq.h>
#include <vector>
#include <xmlrpc-c/base.hpp>
#include <xmlrpc-c/registry.hpp>
#include <xmlrpc-c/server_abyss.hpp>

#include "runcontrol.h"

//#define DEBUG
//#define DEBUG_MORE

#define USB_VENDOR_ID   0x04B4
#define USB_PRODUCT_ID  0x8613
#define USB_TIMEOUT		500
#define EP_DAQRD     	(0x08 | LIBUSB_ENDPOINT_IN)
#define LEN_IN_BUFFER	1024*8

#define MAX_EVENT_SIZE	16000
#define SOE_WORD		   0xD000
#define EOE_MASK		   0xF000

libusb_device_handle *devh = NULL;
uint8_t in_buffer[LEN_IN_BUFFER];

struct libusb_transfer *transfer_daq_in = NULL;
libusb_context *ctx = NULL;

bool cancel_done = false;

/* tid for usb thread */
pthread_t tid;

RunControl RChandle;

/*-- Function declarations -----------------------------------------*/

int usb_close();
void *usb_events_thread(void *);

/* USB callback ----------------------------------------------------*/

void cb_daq_in(struct libusb_transfer *transfer) {

	static std::vector<unsigned short int> chunk;
	unsigned short int *bufusint;
	unsigned short int value;

	chunk.reserve(MAX_EVENT_SIZE);

	if(transfer->status == LIBUSB_TRANSFER_TIMED_OUT) {

      // submit the next transfer
		libusb_submit_transfer(transfer_daq_in);
		//printf("E: LIBUSB_TRANSFER_TIMED_OUT\n");

	} else if(transfer->status == LIBUSB_TRANSFER_CANCELLED) {

		cancel_done = true;
		//printf("E: LIBUSB_TRANSFER_CANCELLED\n");
   
	} else if(transfer->status == LIBUSB_TRANSFER_COMPLETED) {

		// submit the next transfer
		libusb_submit_transfer(transfer_daq_in);

		bufusint = reinterpret_cast<unsigned short int*>(transfer->buffer);
		long int evlen = ((transfer->actual_length/2 * 2) == transfer->actual_length)?transfer->actual_length/2:transfer->actual_length/2 + 1;

		for (long int i=0; i < evlen; i++) {
			value = bufusint[i];
			chunk.push_back(value);

			if((value & 0xF000) == EOE_MASK) {
            
				void **publisher = (void **) transfer->user_data;
				char *blob_data = reinterpret_cast<char *>(chunk.data());
				long int blob_size = chunk.size() * 2;

				zmq_send(*publisher, blob_data, blob_size, 0);

				chunk.clear();
			}

		}	// end for

		if(chunk.size() >= MAX_EVENT_SIZE) {

			chunk.clear();
		}

#ifdef DEBUG_MORE
		unsigned short int *bufusint;
		int buflen;
		int tlen = transfer->actual_length;

		bufusint = reinterpret_cast<unsigned short int*>(transfer->buffer);
		buflen = ((tlen/2 * 2) == tlen)?tlen/2:tlen/2 + 1;      

		for(int i=0; i<buflen; i++)
			printf("%X ", bufusint[i]);
#endif

	}
}

void *usb_events_thread(void *arg) {

	struct timeval tv;
	tv.tv_sec = 0;
	tv.tv_usec = 100000;

	while(1) {
#ifdef DEBUG
		printf("START loop\n");
#endif
		libusb_handle_events_timeout_completed(ctx, &tv, NULL);
#ifdef DEBUG
		printf("END loop\n");
#endif
	}

   return NULL;
}

int usb_close() {
	libusb_close(devh);
	libusb_exit(NULL);

	return 0;
}

/* Run Control classes */

class rc_read_reg: public xmlrpc_c::method
{
public:
   void execute(const xmlrpc_c::paramList& params, xmlrpc_c::value* const retval) {

      int const addr(params.getInt(0));
      params.verifyEnd(1);

      uint16_t value;
      RChandle.read_reg(addr, value);

      *retval = xmlrpc_c::value_int(value);
   }
};

class rc_write_reg: public xmlrpc_c::method
{
public:
   void execute(const xmlrpc_c::paramList& params, xmlrpc_c::value* const retval) { 

      int const addr(params.getInt(0));
      int const value(params.getInt(1));
      params.verifyEnd(2);

      bool rc;
      rc = RChandle.write_reg(addr, value);

      *retval = xmlrpc_c::value_boolean(rc);
   } 
};

/* main */

int main(void) {

	void *context = zmq_ctx_new();
   void *publisher = zmq_socket(context, ZMQ_PUB);
	zmq_bind(publisher, "tcp://0.0.0.0:5000");

   int r;

	r = libusb_init(NULL);
	if(r < 0) {
	   printf("failed to initialise libusb");
		return(-1);
   }

	devh = libusb_open_device_with_vid_pid(ctx, USB_VENDOR_ID, USB_PRODUCT_ID);
	if (!devh) {
		printf("usb device not found");
		return(-1);
	}

	r = libusb_claim_interface(devh, 0);
	if(r < 0) {
		printf("usb claim interface error");
		return(-1);
	}

	r = libusb_set_interface_alt_setting(devh, 0, 1);
	if(r != 0) {
		printf("usb setting interface alternate settings error");
		return(-1);
	} 

   // try to flush RC read endpoint
   uint8_t data[4];
   int len;
   while( libusb_bulk_transfer(devh, EP_RCRD, data, 4, &len, 250) == 0 )
      ; 

	transfer_daq_in = libusb_alloc_transfer(0);
	libusb_fill_bulk_transfer(transfer_daq_in, devh, EP_DAQRD, in_buffer, LEN_IN_BUFFER, cb_daq_in, &publisher, USB_TIMEOUT);

	libusb_submit_transfer(transfer_daq_in);

	// create USB event thread
	pthread_create(&tid, NULL, usb_events_thread, NULL);

   // initialize run control object
   RChandle.init(&devh);

   // XML-RPC server
   xmlrpc_c::registry registry;
   registry.addMethod("readreg", new rc_read_reg);
   registry.addMethod("writereg", new rc_write_reg);
   xmlrpc_c::serverAbyss server(xmlrpc_c::serverAbyss::constrOpt().registryP(&registry).portNumber(4242));
   
   server.run();

   return 0;
}
