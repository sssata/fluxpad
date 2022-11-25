#pragma once

#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/binary_info.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"
#include "hardware/irq.h"

//master contrlled mode should be used in combination with power down mode
#define TLE493D_DEFAULTMODE			MASTERCONTROLLEDMODE

#define TLE493D_STARTUPDELAY		60
#define TLE493D_RESETDELAY			30

#define TLE493D_NUM_OF_REGMASKS		50
#define TLE493D_NUM_OF_ACCMODES		4
#define TLE493D_MSB_MASK			0x07F1
#define TLE493D_LSB_MASK			0x07
#define TLE493D_MAX_THRESHOLD		1023
#define TLE493D_MEASUREMENT_READOUT	7

#define TLE493D_B_MULT 				0.13
#define TLE493D_B_MULT_LOW			2.08 //for 8 bit resolution
#define TLE493D_TEMP_MULT 			0.24 //range 0.21 to 0.27
#define TLE493D_TEMP_MULT_LOW 		3.84 //for 8 bit resolution
#define TLE493D_TEMP_OFFSET 		1180 //range 1000 to 1360
#define TLE493D_TEMP_25				25 	 //room temperature offset


/**
 * @enum Registers_e
 * names of register fields
 */
enum Registers_e
{
	BX1 = 0,
	BX2,
	BY1,
	BY2,
	BZ1,
	BZ2,
	TEMP1,
	TEMP2,
	ID, 							//diagnosis
	P, FF, CF, T, PD_3, PD_0, FRM, 	//diagnosis (Diag)
	XL, 							//wake up threshold MSBs
	XH,
	YL,
	YH,
	ZL,
	ZH,
	WA, WU, XH2, XL2, 				//wake up (WU) & wake up threshold LSBs
	TST, YH2, YL2,					//TMode
	PH, ZH2, ZL2,					//TPhase
	DT, AM, TRIG, X2, TL_mag, CP,	//Config
	FP, IICadr, PR, CA, INT, MODE,	//MOD1
	Res12,
	PRD, Res13,						//MOD2
	Res14,
	Res15, 
	Ver,
};

enum RegisterAddr_e
{
	WAKEUP_REGISTER = 0x0D,
	CONFIG_REGISTER = 0x10,
	MOD1_REGISTER = 0x11,
	MOD2_REGISTER = 0x13,
};

// const RegMask_t regMasks[] = {
// 	{ REGMASK_READ, 0, 0xFF, 0 },		// R_BX1
// 	{ REGMASK_READ, 4, 0xF0, 4 },		// R_BX2
// 	{ REGMASK_READ, 1, 0xFF, 0 },		// R_BY1
// 	{ REGMASK_READ, 4, 0x0F, 0 },		// R_BY2
// 	{ REGMASK_READ, 2, 0xFF, 0 },		// R_BZ1
// 	{ REGMASK_READ, 5, 0x0F, 0 },		// R_BZ2
// 	{ REGMASK_READ, 3, 0xFF, 0 },		// R_TEMP1
// 	{ REGMASK_READ, 5, 0xC0, 6 },		// R_TEMP2
// 	{ REGMASK_READ, 5, 0x30, 4 }, 		// ID
	
// 	{ REGMASK_READ, 6, 0x80, 7},		// P
// 	{ REGMASK_READ, 6, 0x40, 6},		// FF 
// 	{ REGMASK_READ, 6, 0x20, 5},		// CF 
// 	{ REGMASK_READ, 6, 0x10, 4},		// T 
// 	{ REGMASK_READ, 6, 0x08, 3},		// PD_3 
// 	{ REGMASK_READ, 6, 0x04, 2},		// PD_0
// 	{ REGMASK_READ, 6, 0x03, 0},		// FRM
	
// 	{ REGMASK_WRITE, 7, 0xFF, 0},		// XL (MSB)
// 	{ REGMASK_WRITE, 8, 0xFF, 0},		// XH 
// 	{ REGMASK_WRITE, 9, 0xFF, 0},		// YL 
// 	{ REGMASK_WRITE, 10, 0xFF, 0},		// YH 
// 	{ REGMASK_WRITE, 11, 0xFF, 0},		// ZL 
// 	{ REGMASK_WRITE, 12, 0xFF, 0},		// ZH 
	
// 	{ REGMASK_READ, 13, 0x80, 7},		// WA
// 	{ REGMASK_WRITE, 13, 0x40, 6},		// WU
// 	{ REGMASK_WRITE, 13, 0x38, 3},		// XH2 (LSB)
// 	{ REGMASK_WRITE, 13, 0x07, 0},		// XL2
	
// 	{ REGMASK_WRITE, 14, 0xA0, 6 }, 	// TST 
// 	{ REGMASK_WRITE, 14, 0x38, 3 }, 	// YH2
// 	{ REGMASK_WRITE, 14, 0x07, 0 }, 	// YL2 
	
// 	{ REGMASK_WRITE, 15, 0xA0, 6 }, 	// PH 
// 	{ REGMASK_WRITE, 15, 0x38, 3 }, 	// ZH2 
// 	{ REGMASK_WRITE, 15, 0x07, 0 }, 	// ZL2 
	
// 	// CONFIG
// 	{ REGMASK_WRITE, 16, 0x80, 7}, 		// DT
// 	{ REGMASK_WRITE, 16, 0x40, 6}, 		// AM 
// 	{ REGMASK_WRITE, 16, 0x30, 4}, 		// TRIG 
// 	{ REGMASK_WRITE, 16, 0x04, 3}, 		// X2
// 	{ REGMASK_WRITE, 16, 0x03, 1}, 		// TL_mag
// 	{ REGMASK_WRITE, 16, 0x01, 0}, 		// CP 
	
// 	// MOD1
// 	{ REGMASK_WRITE, 17, 0x80, 7}, 		// FP 
// 	{ REGMASK_WRITE, 17, 0x60, 5}, 		// IICadr
// 	{ REGMASK_WRITE, 17, 0x10, 4}, 		// PR
// 	{ REGMASK_WRITE, 17, 0x08, 3}, 		// CA
// 	{ REGMASK_WRITE, 17, 0x04, 2}, 		// INT
// 	{ REGMASK_WRITE, 17, 0x03, 0}, 		// MODE
	
// 	{ REGMASK_WRITE, 18, 0xFF, 0 }, 	// Res12
// 	{ REGMASK_WRITE, 19, 0xE0, 5 }, 	// PRD 
// 	{ REGMASK_WRITE, 19, 0x1F, 0 }, 	// RES13
// 	{ REGMASK_WRITE, 20, 0xFF, 0 }, 	// Res14
// 	{ REGMASK_WRITE, 21, 0xFF, 0 }, 	// Res15
	
// 	{ REGMASK_READ, 22, 0xFF, 0 }, 		// Version 
	
// };

// const uint8_t resetValues[] = {
// 	//register 05h, 11h uses different reset values for different types
// 	//12h 14h 15h are reserved and initialized to 0
// 	//version register (16h) can be initialized with C9h, D9h or E9h
// 	0x80,
// 	0x80, 0x80, 0x80, 0x00, 0x00,
// 	0x60, 0x80, 0x7F, 0x80, 0x7F,
// 	0x80, 0x7F, 0x38, 0x38, 0x38,
// 	0x01, 0x00, 0x00, 0x00, 0x00,
// 	0x00, 0xC9,
// };

enum TLE493D_TypeAddress_e
{
	TLE493D_A0 = 0x35,
	TLE493D_A1 = 0x22,
	TLE493D_A2 = 0x78,
	TLE493D_A3 = 0x44,
};

typedef struct {
	i2c_inst_t* i2c;
	uint8_t i2c_address;
	uint i2c_baudrate;
	uint16_t bx_raw;
	uint16_t by_raw;
	uint16_t bz_raw;
	uint16_t temp_raw;
} TLE493D_t;

/**
 * @brief Creates a TLE493D struct
 * 
 * @param i2c_address i2c address of the sensor, expectes a TLE493D_TypeAddress_e 
 * @param i2c i2c instance, either i2c0 or i2c1
 * @return TLE493D_t 
 */
TLE493D_t tle493d_create(uint8_t i2c_address, i2c_inst_t* i2c, uint baudrate);


/**
 * @brief Initializes the sensor by staring i2c bus and writing config registers
 * 
 * @param TLE493D_t sensor to init 
 * @return int error code
 */
int tle493d_init(TLE493D_t*);

int tle493d_read_blocking(TLE493D_t*);

int tle493d_reset(TLE493D_t*);

/**
 * @return the last X Field read from sensor
 */
float tle493d_get_last_BX(TLE493D_t);
/**
 * @return the last Y Field read from sensor
 */
float tle493d_get_last_BY(TLE493D_t);
/**
 * @return the last Z Field read from sensor
 */
float tle493d_get_last_BZ(TLE493D_t);

/**
 * @return the last temp read from sensor
 */
float tle493d_get_last_temp(TLE493D_t);


