#include "TLE493D.h"

TLE493D_t tle493d_create(uint8_t i2c_address, i2c_inst_t* i2c, uint baudrate){
    TLE493D_t tle493d = {
        .i2c = i2c,
        .i2c_address = i2c_address,
        .i2c_baudrate = baudrate,
        .bx_raw = 0,
        .by_raw = 0,
        .bz_raw = 0,
        .temp_raw = 0,
    };
    return tle493d;
}

int tle493d_init(TLE493D_t* tle493d)
{

    int ret;

    uint8_t data_out [] = {
        // bit 7: disable temp = 1
        // bit 6: disable bz = 1
        // bit 5,4: trigger ADC read before first MSB = 01
        // bit 3: double sensitivity = 1
        // bit 2,1: no temp compensation = 00
        // bit 0: odd parity bit
    // bit76543210
        0b10010000,
        // bit 7: parity
        // bit 6, 5: i2c addr
        // bit 4: one bit read = 1
        // bit 3: disable clock stretch = 1
        // bit 2: disable int = 1
        // bit 1,0: mode
    // bit76543210
        0b00011101,
    };

    printf("tle init\n");
    ret = i2c_write_timeout_us(tle493d->i2c, tle493d->i2c_address, data_out, sizeof(data_out), false, 1000u);
    if (ret < 0){
        printf("ret: %d\n", ret);
        return ret;
    }

    return ret;

};

int tle493d_read_blocking(TLE493D_t* tle493d){
    printf("tle read\n");
    int ret;

    struct data_in_buf_t{
        uint8_t bx_hi;
        uint8_t by_hi;
        uint8_t bz_hi;
        uint8_t temp_hi;
        uint8_t bx_lo:4;
        uint8_t by_lo:4;
        uint8_t temp_lo:2;
        uint8_t id:2;
        uint8_t bz_lo:4;
        uint8_t diag;
    } __attribute__((__packed__)) data_in_buf;
    ret = i2c_read_timeout_us(tle493d->i2c, tle493d->i2c_address, (uint8_t*) &data_in_buf, sizeof(data_in_buf), false, 1000u);

    if (ret < 0){
        printf("ret: %d\n", ret);
        return ret;
    }
    printf("id: %x\n",data_in_buf.id);
    printf("temp_hi: %x\n",data_in_buf.temp_hi);
    printf("temp_lo: %x\n",data_in_buf.temp_lo);
    printf("diag: %x\n", data_in_buf.diag);

    tle493d->bx_raw = data_in_buf.bx_hi << 4 & data_in_buf.bx_lo;
    tle493d->by_raw = data_in_buf.by_hi << 4 & data_in_buf.by_lo;
    tle493d->bz_raw = data_in_buf.bz_hi << 4 & data_in_buf.bz_lo;
    tle493d->temp_raw = data_in_buf.temp_hi << 4 & data_in_buf.temp_lo;
    printf("bz_raw: %d\n", tle493d->bz_raw);
    printf("by_raw: %d\n", tle493d->by_raw);

    return ret;
}
