#include <EEPROM.h>
#include <Keyboard.h>
#include <tusb_config.h>


void setup()
{
	Keyboard.begin();
}

void loop()
{
	Keyboard.press()
}
