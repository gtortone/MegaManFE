#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <libusb-1.0/libusb.h>
#include <zmq.hpp>

//#define DEBUG
//#define DEBUG_MORE

#define USB_VENDOR_ID   0x04B4
#define USB_PRODUCT_ID  0x8613
#define USB_TIMEOUT		500
#define EP_DAQRD     	(0x08 | LIBUSB_ENDPOINT_IN)
#define LEN_IN_BUFFER	1024*8

libusb_device_handle *devh = NULL;
uint8_t in_buffer[LEN_IN_BUFFER];

struct libusb_transfer *transfer_daq_in = NULL;
libusb_context *ctx = NULL;

bool cancel_done = false;

/* tid for usb thread */
pthread_t tid;
pthread_mutex_t mutex;

#define SOE	0xD000

/*-- Function declarations -----------------------------------------*/

int usb_close();
void *usb_events_thread(void *);

/* USB callback ----------------------------------------------------*/

void cb_daq_in(struct libusb_transfer *transfer) {

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

		zmq::socket_t *publisher = (zmq::socket_t *) transfer->user_data;
		//printf("length: %d - actual_length %d\n", transfer->length, transfer->actual_length);
		publisher->send(transfer->buffer, transfer->actual_length);

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

int main(void) {

	zmq::context_t context(1);
	zmq::socket_t publisher(context, ZMQ_PUB);
   int r;

	publisher.bind("tcp://0.0.0.0:5000");

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

	transfer_daq_in = libusb_alloc_transfer(0);
	libusb_fill_bulk_transfer(transfer_daq_in, devh, EP_DAQRD, in_buffer, LEN_IN_BUFFER, cb_daq_in, &publisher, USB_TIMEOUT);

	if( pthread_mutex_init(&mutex, NULL) != 0 ) {
		printf("mutex initialization error");
		return(-1);
	}

	libusb_submit_transfer(transfer_daq_in);

	// create USB event thread
	pthread_create(&tid, NULL, usb_events_thread, NULL);

	while(1) {
		sleep(1);
	}
}
