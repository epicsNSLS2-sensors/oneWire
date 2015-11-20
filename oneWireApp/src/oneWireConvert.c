
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <ctype.h>
#include <math.h>

#include <dbAccess.h>
#include <dbDefs.h>
#include <dbFldTypes.h>
#include <registryFunction.h>
#include <aSubRecord.h>
#include <waveformRecord.h>
#include <epicsExport.h>
#include <epicsTime.h>

#define MASS_STRING	10
#define VAL_STRING	20
#define MASS_TOTAL	5000
#define MEAS_STRING	10000

int onewire_aSubDebug = 0;

int ch2hex(char ch)
{
	if (isdigit(ch))	
		return ch - '0';
	if (islower(ch))	
		return ch - 'a' + 10;
	if (isupper(ch))	
		return ch - 'A' + 10;
}

int str2hex(char arr[2])
{
	return (ch2hex(arr[0]) << 4 | ch2hex(arr[1]));
}

static long aSubConvertDS2438Init(aSubRecord* paSub) 
{
	if (onewire_aSubDebug)
        	printf("Record %s called aSubConvertDS2438Init(%p)\n",paSub->name, (void*) paSub);

	return 0; 
}

static long aSubConvertDS2438Page0(aSubRecord *paSub)
{
	char *aptr, byte_hex[2];
	int byte[8];
	int i;
	int tempWhole;
	double temp, tempFrac;
	double Vdd, Vsens;
	
	if (onewire_aSubDebug)
	{
		printf("Record %s called aSubConvertDS2438Page0(%p)\n",paSub->name, (void*) paSub);
	}

	/* Get the result */
	aptr = (char *)paSub->a;
/*	printf("Raw data is %s\n", aptr);*/

	/* Parse the results into 8 bytes */
	for(i = 0; i < 8; i++)
	{
		strncpy(byte_hex, aptr + i * 2, 2 * sizeof(char));  
		byte_hex[2] = '\0';
		byte[i] = str2hex(byte_hex);
/*		printf("raw data is %s, byte in int is %d\n", byte_hex, byte[i]);*/
	}		
		
	/* Temperature conversion */
	if (byte[2] & 0x80)
	{
		/* Negative temperature */
		tempWhole = ~ byte[2];
		tempFrac = ((~ byte[1]) & 0xF8) * pow(2, -8);
		temp = -1 * (tempWhole + tempFrac);
/*		printf("temp whole is %d, frac is %f, total is %f\n", tempWhole, tempFrac, temp);*/
	}
	else
	{
		/* Positive temperature */
		tempWhole = byte[2];
		tempFrac = (byte[1] & 0xF8) * pow(2, -8);
		temp = tempWhole + tempFrac;
/*		printf("temp whole is %d, frac is %f, total is %f\n", tempWhole, tempFrac, temp);*/
	}

	/* Vdd unit is 10 mV, that 0.01 */
	Vdd = (( byte[3] + (byte[4] * 0xFF)) & 0x3FF) * 0.01;  

	/* I = Vsens register / (4096 * R) */
	/* Vsens = Vsens register / 4096, unit = 0.2441mV */
	Vsens = (( byte[5] + (byte[6] * 0xFF)) & 0x3FF) * 0.0002441;
/*	printf("Vdd is %f, Vsens is %f\n", Vdd, Vsens);*/

	memcpy((double *)paSub->vala, &temp, paSub->nova*sizeof(double));
	memcpy((double *)paSub->valb, &Vdd, paSub->novb*sizeof(double));
	memcpy((double *)paSub->valc, &Vsens, paSub->novc*sizeof(double));

	paSub->pact = FALSE;

	return(0);
}

static long aSubConvertDS2438Page6(aSubRecord *paSub)
{
	char *aptr, byte_hex[2];
	int byte[8];
	int i;
	double offset, slope;
	
	if (onewire_aSubDebug)
	{
		printf("Record %s called aSubConvertDS2438Page6(%p)\n",paSub->name, (void*) paSub);
	}

	/* Get the result */
	aptr = (char *)paSub->a;
/*	printf("Raw data is %s\n", aptr);*/

	/* Parse the results into 8 bytes */
	for(i = 0; i < 8; i++)
	{
		strncpy(byte_hex, aptr + i * 2, 2 * sizeof(char));  
		byte_hex[2] = '\0';
		byte[i] = str2hex(byte_hex);
/*		printf("raw data is %s, byte in int is %d\n", byte_hex, byte[i]);*/
	}		
		
	/* Offset conversion */
	offset = ( byte[2] * 0xFF + byte[3] ) / 10000.0000;
/*	printf("%d, %d \t",  byte[2] * 0xFF + byte[3],  byte[4] * 0xFF + byte[5]);*/

	/* Slop conversion */
	slope = ( byte[4] * 0xFF + byte[5] ) / 100000.0000;
/*	printf("offset is %f, slope is %f\n", offset, slope);*/

	memcpy((double *)paSub->vala, &offset, paSub->nova*sizeof(double));
	memcpy((double *)paSub->valb, &slope, paSub->novb*sizeof(double));

	paSub->pact = FALSE;

	return(0);
}

static long aSubConvertDS18B20Init(aSubRecord* paSub) 
{
	if (onewire_aSubDebug)
        	printf("Record %s called aSubConvertDS18B20Init(%p)\n",paSub->name, (void*) paSub);

	return 0; 
}

static long aSubConvertDS18B20Proc(aSubRecord *paSub)
{
	char *aptr, byte_hex[2];
	int byte[8];
	int i;
	double temp, tempFrac;
	int tempWhole, tempHi, tempLo;
		
	if (onewire_aSubDebug)
	{
		printf("Record %s called aSubConvertDS18B20Proc(%p)\n",paSub->name, (void*) paSub);
	}

	/* Get the result */
	aptr = (char *)paSub->a;
/*	printf("Raw data is %s\n", aptr);*/

	/* Parse the results into 8 bytes */
	for(i = 0; i < 8; i++)
	{
		strncpy(byte_hex, aptr + i * 2, 2 * sizeof(char));  
		byte_hex[2] = '\0';
		byte[i] = str2hex(byte_hex);
/*		printf("raw data is %s, byte in int is %d\n", byte_hex, byte[i]);*/
	}		
		
	/* Temperature conversion */
	if (byte[1] & 0xF8)
	{
		/* Negative temperature */
		tempWhole = (~(byte[1] << 4 | ch2hex(aptr[0]))) & 0xF8;
		tempFrac = (~(ch2hex(aptr[1])) & 0xF8) * pow(2, -4);
		temp = -1 * (tempWhole + tempFrac);
/*		printf("temp whole is %d, frac is %f, total is %f\n", tempWhole, tempFrac, temp);*/
	}
	else
	{
		/* Positive temperature */
		tempWhole = byte[1] << 4 | ch2hex(aptr[0]);
		tempFrac = ch2hex(aptr[1]) * pow(2, -4);
		temp = tempWhole + tempFrac;
/*		printf("temp whole is %d, frac is %f, total is %f\n", tempWhole, tempFrac, temp);*/
	}

	/* Temperature high alarm */	
	if (byte[2] & 0x80)
		/* Negative temperature */
		tempHi = ((~byte[2]) & 0xF8 ) * -1;
	else
		tempHi = byte[2];

	/* Temperature lo alarm */	
	if (byte[3] & 0x80)
		/* Negative temperature */
		tempLo = ((~byte[3]) & 0xF8 ) * -1;
	else
		tempLo = byte[3];

/*	printf("Temp Hi is %d, Lo is %d\n", tempHi, tempLo);*/

	memcpy((double *)paSub->vala, &temp, paSub->nova*sizeof(double));
	memcpy((short *)paSub->valb, &tempHi, paSub->novb*sizeof(short));
	memcpy((short *)paSub->valc, &tempLo, paSub->novc*sizeof(short));

	paSub->pact = FALSE;

	return(0);
}

/* Register these symbols for use by IOC code: */
epicsExportAddress(int, onewire_aSubDebug);
epicsRegisterFunction(aSubConvertDS2438Init);
epicsRegisterFunction(aSubConvertDS2438Page0);
epicsRegisterFunction(aSubConvertDS2438Page6);
epicsRegisterFunction(aSubConvertDS18B20Init);
epicsRegisterFunction(aSubConvertDS18B20Proc);



