TOP=../..

include $(TOP)/configure/CONFIG
#=============================
# Build the IOC application

PROD_IOC = oneWire
# oneWire.dbd will be created and installed
DBD += oneWire.dbd

# oneWire.dbd will be made up from these files:
oneWire_DBD += base.dbd
oneWire_DBD += asyn.dbd
oneWire_DBD += stream.dbd
oneWire_DBD += drvAsynIPPort.dbd
oneWire_DBD += oneWireConvert.dbd

# oneWire_registerRecordDeviceDriver.cpp derives from oneWire.dbd
oneWire_SRCS += oneWire_registerRecordDeviceDriver.cpp

oneWire_SRCS += oneWireConvert.c

# Build the main IOC entry point on workstation OSs.
oneWire_SRCS_DEFAULT += oneWireMain.cpp
oneWire_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#oneWire_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Link in the code from the support library
oneWire_LIBS += asyn stream

# Finally link to the EPICS Base libraries
oneWire_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

